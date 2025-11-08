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
SUMIDA_CSV_URL = "https://www.opendata.metro.tokyo.lg.jp/sumida/131075_public_toilet.csv"
SHINJUKU_CSV_URL = "https://www.city.shinjuku.lg.jp/content/000399974.csv"

# -----------------------------------------------------------------
# 2. データ取得関数群
# -----------------------------------------------------------------

def get_sumida_data():
    """ 墨田区のデータをCSVから取得・加工 """
    print("墨田区のデータを取得します(CSV)...")
    try:
        # 墨田区はUTF-8またはcp932を想定
        try:
            df = pd.read_csv(SUMIDA_CSV_URL, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(SUMIDA_CSV_URL, encoding="cp932", errors='replace')

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')):
                continue

            processed_data.append({
                "name": row.get("名称"),
                "address": row.get("所在地"),
                "latitude": float(row.get("緯度")),
                "longitude": float(row.get("経度")),
                "opening_hours": None, 
                "availability_notes": None,
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
        
        # ★修正: UTF-16 でデコードを試みる
        try:
            # 'utf-16' は BOM の有無を自動判定してくれます
            df = pd.read_csv(io.BytesIO(response.content), encoding='utf-16', sep='\t') 
            # ※ UTF-16のCSVはタブ区切り(TSV)になっていることも多いため、sep='\t' も試す価値あり。
            # もしカンマ区切りなら sep=',' (デフォルト) に戻してください。
            # 一旦、標準的なカンマ区切りと仮定して sep 指定なしで試してみます↓
            # df = pd.read_csv(io.BytesIO(response.content), encoding='utf-16')
            
            # もし上記で「1列しか認識されない」などの場合は、区切り文字が違う可能性があります。
            # エラーが出る場合は、以下のいずれかを試してみてください:
            # df = pd.read_csv(io.BytesIO(response.content), encoding='utf-16', sep='\t')
             
        except Exception:
             # UTF-16で失敗した場合の予備（念のため）
             df = pd.read_csv(io.BytesIO(response.content), encoding='cp932', errors='replace')

        # もしカンマ区切りで正しく読めていれば、カラム名が認識されているはず
        if '緯度' not in df.columns:
             # カンマじゃなかった可能性が高いので、タブ区切りで再トライ
             print("  (カンマ区切りで失敗したため、タブ区切りで再試行します...)")
             df = pd.read_csv(io.BytesIO(response.content), encoding='utf-16', sep='\t')

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
    # ... (省略) ...
    return []

# -----------------------------------------------------------------
# 3. Supabase更新関数 (変更なし)
# -----------------------------------------------------------------
def update_supabase(data_list):
    """ 収集したデータをSupabaseにInsertする """
    if not data_list:
        print("更新対象のデータがありません。")
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"Supabaseに {len(data_list)} 件のデータを Insert (挿入) します...")
        CHUNK_SIZE = 500 
        for i in range(0, len(data_list), CHUNK_SIZE):
            chunk = data_list[i:i + CHUNK_SIZE]
            supabase.table(TABLE_NAME).insert(chunk).execute()
            print(f"  ... {min(i + CHUNK_SIZE, len(data_list))} / {len(data_list)} 件 処理完了")
        print("\nデータの同期が正常に完了しました！")
    except Exception as e:
        print(f"\nエラー(Supabase): データベースの更新に失敗しました。")
        print(f"  エラー本体: {e}")

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
    all_toilet_data.extend(get_sumida_data())
    all_toilet_data.extend(get_shinjuku_data())
    all_toilet_data.extend(get_station_data_from_csv())
    all_toilet_data.extend(get_new_ward_data_template()) 

    print(f"\n合計 {len(all_toilet_data)} 件のデータを収集しました。")
    update_supabase(all_toilet_data)

    elapsed_time = time.time() - start_time
    print(f"=== 処理完了 (所要時間: {elapsed_time:.2f}秒) ===")

if __name__ == "__main__":
    main()