import os
import requests
import pandas as pd
import io
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from station_data_importer import get_station_data_from_csv

# -----------------------------------------------------------------
# 1. 設定
# -----------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME = 'toilets'

# 各自治体のデータURL
# 墨田区 (CSVに変更)
SUMIDA_CSV_URL = "https://www.opendata.metro.tokyo.lg.jp/sumida/131075_public_toilet.csv"
# 新宿区 (CSV)
SHINJUKU_CSV_URL = "https://www.city.shinjuku.lg.jp/content/000399974.csv"

# -----------------------------------------------------------------
# 2. データ取得関数群
# -----------------------------------------------------------------

def get_sumida_data():
    """ 墨田区のデータをCSVから取得・加工 """
    print("墨田区のデータを取得します(CSV)...")
    try:
        # CSVを読み込む (文字コードはUTF-8と想定、ダメならcp932を試す)
        try:
            df = pd.read_csv(SUMIDA_CSV_URL, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(SUMIDA_CSV_URL, encoding="cp932")

        processed_data = []
        for _, row in df.iterrows():
            # 緯度経度が取得できないデータは除外
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')):
                continue

            processed_data.append({
                "name": row.get("名称"),      # カラム名をCSVに合わせて変更
                "address": row.get("所在地"), # カラム名をCSVに合わせて変更
                "latitude": float(row.get("緯度")),
                "longitude": float(row.get("経度")),
                # 墨田区CSVには営業時間などの情報がない場合が多いのでNone
                "opening_hours": None, 
                "availability_notes": None,
                # 設備情報もCSVに含まれていなければ全てFalseまたは不明とする
                # もし「多機能トイレ」などのカラムがあれば、以下のように設定可能
                # "is_wheelchair_accessible": row.get("多機能トイレ") == "有",
                "is_wheelchair_accessible": False, 
                "has_diaper_changing_station": False,
                "is_ostomate_accessible": False,
                "is_station_toilet": False,
                "inside_gate": False,
                "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            })
        print(f"墨田区: {len(processed_data)} 件取得しました。")
        return processed_data
    except Exception as e:
        print(f"墨田区データの取得に失敗しました: {e}")
        return []

def get_shinjuku_data():
    """ 新宿区のデータを取得・加工 """
    print("新宿区のデータを取得します...")
    try:
        response = requests.get(SHINJUKU_CSV_URL)
        response.raise_for_status()
        
        # 文字コード判定（UTF-8を先に試し、ダメならCP932）
        try:
            csv_data = response.content.decode('utf-8')
        except UnicodeDecodeError:
            csv_data = response.content.decode('cp932')
            
        df = pd.read_csv(io.StringIO(csv_data))

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')):
                continue

            processed_data.append({
                "name": row.get("名称"),
                "address": row.get("所在地"),
                "latitude": float(row.get("緯度")),
                "longitude": float(row.get("経度")),
                "opening_hours": row.get("供用時間"),
                "availability_notes": None,
                "is_wheelchair_accessible": row.get("設置（車いす）") == "○",
                "has_diaper_changing_station": row.get("設置（ベビーベッド）") == "○" or row.get("設置（ベビーチェア）") == "○",
                "is_ostomate_accessible": row.get("設置（オストメイト）") == "○",
                "is_station_toilet": False,
                "inside_gate": False,
                "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            })
        print(f"新宿区: {len(processed_data)} 件取得しました。")
        return processed_data
    except Exception as e:
        print(f"新宿区データの取得に失敗しました: {e}")
        return []

# =================================================================
# ★ 新規追加用テンプレート関数 (変更なし) ★
# =================================================================
def get_new_ward_data_template():
    # ... (省略: 前回のコードと同じ) ...
    ward_name = "〇〇区"
    # ...
    return []

# -----------------------------------------------------------------
# 3. Supabase更新関数 (Upsertに変更済み)
# -----------------------------------------------------------------
def update_supabase(data_list):
    """ 収集したデータをSupabaseにアップサートする """
    if not data_list:
        print("更新対象のデータがありません。")
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 全件削除は廃止 (外部キー制約のため)
        # print("既存のデータを削除しています...")
        # supabase.table(TABLE_NAME).delete().gt('created_at', '1970-01-01').execute()

        print(f"Supabaseに {len(data_list)} 件のデータを Upsert (更新・挿入) します...")
        
        CHUNK_SIZE = 500 
        for i in range(0, len(data_list), CHUNK_SIZE):
            chunk = data_list[i:i + CHUNK_SIZE]
            # upsert を使用（on_conflict に一意なカラムを指定する必要があるが、
            # 現状は name と address の複合キーなどが候補。
            # 一旦は単純な insert で進めるが、重複の可能性あり。
            # 本格運用時は、各データに一意な ID (例: "sumida_001") を生成して付与することを推奨）
            supabase.table(TABLE_NAME).upsert(chunk).execute() 
            
            print(f"  ... {min(i + CHUNK_SIZE, len(data_list))} / {len(data_list)} 件 処理完了")

        print("\nデータの同期が正常に完了しました！")
    except Exception as e:
        print(f"\nエラー(Supabase): データベースの更新に失敗しました。")
        if hasattr(e, 'details'): print(f"  詳細: {e.details}")
        elif hasattr(e, 'message'): print(f"  詳細: {e.message}")
        else: print(f"  詳細: {e}")

# -----------------------------------------------------------------
# 4. メイン実行処理
# -----------------------------------------------------------------
def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("エラー: 環境変数 SUPABASE_URL または SUPABASE_KEY が設定されていません。")
        return

    print("=== トイレデータ同期バッチを開始します ===")
    start_time = time.time()

    all_toilet_data = []

    # 1. 墨田区 (CSV)
    all_toilet_data.extend(get_sumida_data())
    
    # 2. 新宿区 (CSV)
    all_toilet_data.extend(get_shinjuku_data())

    # 3. 駅トイレ (ローカルCSV)
    all_toilet_data.extend(get_station_data_from_csv())

    # 4. その他
    all_toilet_data.extend(get_new_ward_data_template()) 

    print(f"\n合計 {len(all_toilet_data)} 件のデータを収集しました。")
    update_supabase(all_toilet_data)

    elapsed_time = time.time() - start_time
    print(f"=== 処理完了 (所要時間: {elapsed_time:.2f}秒) ===")

if __name__ == "__main__":
    main()