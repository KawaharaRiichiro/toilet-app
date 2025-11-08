import os
import requests
import pandas as pd
import io
from supabase import create_client, Client
from dotenv import load_dotenv
import time
# 既存の駅データインポーター
from station_data_importer import get_station_data_from_csv

# -----------------------------------------------------------------
# 1. 設定
# -----------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME = 'toilets'

# 各自治体のデータURL
SUMIDA_API_URL = "https://service.api.metro.tokyo.lg.jp/api/t131075d0000000137-955e33d5f6e6df2b07b523cd05679ad3-0/json"
SHINJUKU_CSV_URL = "https://www.city.shinjuku.lg.jp/content/000399974.csv"

# -----------------------------------------------------------------
# 2. データ取得関数群
# -----------------------------------------------------------------

def get_sumida_data():
    """ 墨田区のデータを取得・加工 """
    print("墨田区のデータを取得します...")
    try:
        response = requests.get(SUMIDA_API_URL)
        response.raise_for_status()
        data = response.json()

        processed_data = []
        for item in data:
            # 緯度経度が取得できないデータは除外
            if not item.get('place_lat') or not item.get('place_lon'):
                continue

            processed_data.append({
                "name": item.get("facility_name"),
                "address": item.get("address"),
                "latitude": float(item.get("place_lat")),
                "longitude": float(item.get("place_lon")),
                "opening_hours": None, # APIに応じた加工が必要ならここに追加
                "availability_notes": None,
                # 以下、元データに項目があれば適宜マッピングを変更してください
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
        
        # Shift-JISでデコードしてpandasで読み込む
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
                # 新宿区CSVの実際のカラム名に合わせて調整してください
                # 例: "設置（車いす）" カラムが "○" なら True にするなど
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
# ★ 新規追加用テンプレート関数 ★
# 新しい自治体を追加する際は、この関数をコピーして作成してください。
# =================================================================
def get_new_ward_data_template():
    """
    (テンプレート) 新しい自治体のデータを取得・加工する関数
    """
    # 1. 対象の自治体名に変更してください
    ward_name = "〇〇区" 
    print(f"{ward_name}のデータを取得します(テンプレート実行)...")
    
    # 2. 実際のCSVなどのURLを設定してください
    URL = "" 
    
    # URLが設定されていない場合は空リストを返して終了（エラー回避用）
    if not URL:
        print(f"※{ward_name}のURLが未設定のためスキップします。")
        return []

    try:
        # 3. データの読み込み（CSVの場合の例）
        # response = requests.get(URL)
        # response.raise_for_status()
        # df = pd.read_csv(io.BytesIO(response.content), encoding='utf-8') # 文字コードは適宜変更(cp932など)

        processed_data = []
        # 4. ループ処理でSupabase形式に変換
        # for _, row in df.iterrows():
        #     if pd.isna(row.get('緯度カラム名')) or pd.isna(row.get('経度カラム名')):
        #         continue
        #
        #     processed_data.append({
        #         "name": row.get("名称カラム名"),
        #         "address": row.get("住所カラム名"),
        #         "latitude": float(row.get("緯度カラム名")),
        #         "longitude": float(row.get("経度カラム名")),
        #         # ... 他の項目もマッピング ...
        #         "is_station_toilet": False,
        #         "inside_gate": False,
        #         "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        #         "updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        #     })

        print(f"{ward_name}: {len(processed_data)} 件取得しました。")
        return processed_data
    except Exception as e:
        print(f"{ward_name}データの取得に失敗しました: {e}")
        return []

# -----------------------------------------------------------------
# 3. Supabase更新関数 (変更なし)
# -----------------------------------------------------------------
def update_supabase(data_list):
    """ 収集したデータをSupabaseにアップサート（洗い替え）する """
    if not data_list:
        print("更新対象のデータがありません。")
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        print("既存のデータを削除しています...")
        # 全件削除（注意: 本番環境では運用に合わせて調整してください）
        supabase.table(TABLE_NAME).delete().gt('created_at', '1970-01-01').execute()
        print("既存データの削除が完了しました。")

        print(f"Supabaseに {len(data_list)} 件のデータを Insert (挿入) します...")
        
        # 一度に大量のデータを送るとエラーになることがあるため、分割して送信
        CHUNK_SIZE = 500 
        for i in range(0, len(data_list), CHUNK_SIZE):
            chunk = data_list[i:i + CHUNK_SIZE]
            supabase.table(TABLE_NAME).insert(chunk).execute()
            print(f"  ... {min(i + CHUNK_SIZE, len(data_list))} / {len(data_list)} 件 挿入完了")

        print("\nデータの同期が正常に完了しました！")
    except Exception as e:
        print(f"\nエラー(Supabase): データベースの更新に失敗しました。")
        # エラー詳細の表示を試みる
        if hasattr(e, 'details'): print(f"  詳細: {e.details}")
        elif hasattr(e, 'message'): print(f"  詳細: {e.message}")
        else: print(f"  詳細: {e}")

# -----------------------------------------------------------------
# 4. メイン実行処理
# -----------------------------------------------------------------
def main():
    # 環境変数のチェック
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("エラー: 環境変数 SUPABASE_URL または SUPABASE_KEY が設定されていません。")
        print(".env ファイルを作成し、設定してください。")
        return

    print("=== トイレデータ同期バッチを開始します ===")
    start_time = time.time()

    # 全データを格納するリスト
    all_toilet_data = []

    # -------------------------------------------------
    # 各ソースからデータを収集
    # -------------------------------------------------
    # 1. 墨田区 (API)
    all_toilet_data.extend(get_sumida_data())
    
    # 2. 新宿区 (CSV)
    all_toilet_data.extend(get_shinjuku_data())

    # 3. 駅トイレ (ローカルCSV)
    # station_data_importer.py からインポートした関数を使用
    all_toilet_data.extend(get_station_data_from_csv())

    # 4. その他の自治体 (ここに追加していく)
    # 例: all_toilet_data.extend(get_shibuya_data())
    all_toilet_data.extend(get_new_ward_data_template()) 

    # -------------------------------------------------
    # データベースを更新
    # -------------------------------------------------
    print(f"\n合計 {len(all_toilet_data)} 件のデータを収集しました。")
    update_supabase(all_toilet_data)

    elapsed_time = time.time() - start_time
    print(f"=== 処理完了 (所要時間: {elapsed_time:.2f}秒) ===")

if __name__ == "__main__":
    main()