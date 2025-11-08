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
SETAGAYA_EXCEL_URL = "https://www.city.setagaya.lg.jp/documents/4424/toilet2024.xlsx"
# ★新規追加: 中野区
NAKANO_CSV_URL = "https://www2.wagmap.jp/nakanodatamap/nakanodatamap/opendatafile/map_50/CSV/opendata_550070.csv"

# -----------------------------------------------------------------
# 2. データ取得関数群
# -----------------------------------------------------------------

def get_sumida_data():
    """ 墨田区のデータをCSVから取得・加工 """
    print("墨田区のデータを取得します(CSV)...")
    try:
        try:
            df = pd.read_csv(SUMIDA_CSV_URL, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(SUMIDA_CSV_URL, encoding="cp932", errors="replace")

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')): continue

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
        
        df = None
        try:
            df = pd.read_csv(io.BytesIO(response.content), encoding='utf-16', sep=',')
        except Exception: pass
            
        if df is None or '緯度' not in df.columns:
             try:
                df = pd.read_csv(io.BytesIO(response.content), encoding='cp932', sep=',', errors='replace')
             except Exception: pass

        if df is None or '緯度' not in df.columns:
             try:
                df = pd.read_csv(io.BytesIO(response.content), encoding='utf-8', sep=',', errors='replace')
             except Exception: pass

        if df is None or '緯度' not in df.columns:
             print("エラー: 新宿区のCSVを正しい文字コードで読み込めませんでした。")
             return []

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')): continue

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

def get_setagaya_data():
    """ 世田谷区のデータをExcelから取得・加工 (メンテナンス明け用) """
    print("世田谷区のデータを取得します(Excel)...")
    try:
        response = requests.get(SETAGAYA_EXCEL_URL)
        if response.status_code != 200:
             print(f"スキップ: 世田谷区データの取得に失敗しました (Status: {response.status_code})")
             return []

        try:
            df = pd.read_excel(io.BytesIO(response.content))
        except Exception as e:
            print(f"エラー: Excelファイルの読み込みに失敗しました: {e}")
            return []

        name_col = next((col for col in ['名称', '施設名', 'トイレ名'] if col in df.columns), None)
        address_col = next((col for col in ['住所', '所在地', '設置場所'] if col in df.columns), None)
        lat_col = next((col for col in ['緯度', 'lat'] if col in df.columns), None)
        lon_col = next((col for col in ['経度', 'lon', 'lng'] if col in df.columns), None)

        if not all([name_col, lat_col, lon_col]):
            print(f"エラー(世田谷区): 必須カラムが見つかりませんでした。")
            return []

        processed_data = []
        for _, row in df.iterrows():
            try:
                lat = float(row.get(lat_col))
                lon = float(row.get(lon_col))
                if pd.isna(lat) or pd.isna(lon): continue
            except (ValueError, TypeError): continue

            processed_data.append({
                "name": row.get(name_col),
                "address": row.get(address_col),
                "latitude": lat,
                "longitude": lon,
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
        print(f"世田谷区: {len(processed_data)} 件取得しました。")
        return processed_data
    except Exception as e:
        print(f"世田谷区データの取得に失敗しました: {e}")
        return []

# ★★★ 新規追加: 中野区データ取得関数 ★★★
def get_nakano_data():
    """ 中野区のデータをCSVから取得・加工 """
    print("中野区のデータを取得します...")
    try:
        response = requests.get(NAKANO_CSV_URL)
        response.raise_for_status()

        # 文字コード判定 (CP932 または UTF-8 を想定)
        df = None
        for encoding in ['cp932', 'utf-8']:
            try:
                df_temp = pd.read_csv(io.BytesIO(response.content), encoding=encoding)
                if '緯度' in df_temp.columns and '経度' in df_temp.columns:
                    df = df_temp
                    break
            except: pass
        
        if df is None:
             print("エラー: 中野区のCSVを読み込めませんでした。")
             return []

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')): continue

            # 設備情報の判定ロジック ("あり" または "1" などをTrueとみなす)
            def is_available(val):
                return str(val).strip() in ['あり', '1', '○', 'TRUE', 'True']

            processed_data.append({
                "name": row.get("名称"),
                "address": row.get("住所"),
                "latitude": float(row.get("緯度")),
                "longitude": float(row.get("経度")),
                "opening_hours": row.get("備考") if pd.notna(row.get("備考")) else None,
                "availability_notes": None,
                "is_wheelchair_accessible": is_available(row.get("車いす使用者用トイレ")),
                "has_diaper_changing_station": is_available(row.get("ベビーシート")) or is_available(row.get("ベビーチェア")),
                "is_ostomate_accessible": is_available(row.get("オストメイト")),
                "is_station_toilet": False,
                "inside_gate": False,
                "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            })
        print(f"中野区: {len(processed_data)} 件取得しました。")
        return processed_data

    except Exception as e:
        print(f"中野区データの取得に失敗しました: {e}")
        return []

# -----------------------------------------------------------------
# 3. Supabase更新関数
# -----------------------------------------------------------------
def update_supabase(data_list):
    if not data_list:
        print("更新対象のデータがありません。")
        return
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"Supabaseに {len(data_list)} 件のデータを Insert します...")
        CHUNK_SIZE = 500 
        for i in range(0, len(data_list), CHUNK_SIZE):
            chunk = data_list[i:i + CHUNK_SIZE]
            supabase.table(TABLE_NAME).insert(chunk).execute()
            print(f"  ... {min(i + CHUNK_SIZE, len(data_list))} / {len(data_list)} 件 処理完了")
        print("\nデータの同期が正常に完了しました！")
    except Exception as e:
        print(f"\nエラー(Supabase): {e}")
        if hasattr(e, 'details'): print(f"  詳細: {e.details}")

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
    all_toilet_data.extend(get_setagaya_data()) # メンテナンス明けに有効化
    all_toilet_data.extend(get_nakano_data())   # ★中野区追加
    all_toilet_data.extend(get_station_data_from_csv())

    print(f"\n合計 {len(all_toilet_data)} 件のデータを収集しました。")
    update_supabase(all_toilet_data)

    elapsed_time = time.time() - start_time
    print(f"=== 処理完了 (所要時間: {elapsed_time:.2f}秒) ===")

if __name__ == "__main__":
    main()