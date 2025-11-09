import os
import requests
import pandas as pd
import io
import uuid
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
TABLE_NAME_TOILETS = 'toilets'
TABLE_NAME_DOORS = 'station_platform_doors'

# 各データのURL
SUMIDA_CSV_URL = "https://www.opendata.metro.tokyo.lg.jp/sumida/131075_public_toilet.csv"
SHINJUKU_CSV_URL = "https://www.city.shinjuku.lg.jp/content/000399974.csv"
NAKANO_CSV_URL = "https://www2.wagmap.jp/nakanodatamap/nakanodatamap/opendatafile/map_50/CSV/opendata_550070.csv"
CHUO_CSV_URL = "https://www.city.chuo.lg.jp/documents/984/kousyuutoilet.csv"

STATION_DOORS_CSV = "station_doors.csv"

# -----------------------------------------------------------------
# 2. データ取得関数群
# -----------------------------------------------------------------

def find_address(row):
    """ 住所カラムを複数の候補から探すヘルパー """
    return row.get("所在地_連結表記") or row.get("所在地") or row.get("住所")

def get_sumida_data():
    print("墨田区のデータを取得します(CSV)...")
    try:
        df = None
        # 墨田区データの読み込み試行
        for encoding in ['utf-8', 'cp932']:
            try:
                df = pd.read_csv(SUMIDA_CSV_URL, encoding=encoding)
                break
            except: continue
            
        if df is None:
             print("エラー: 墨田区のCSVを読み込めませんでした。")
             return []

        processed_data = []
        for _, row in df.iterrows():
            lat = row.get("緯度") or row.get("lat")
            lon = row.get("経度") or row.get("lon")
            if pd.isna(lat) or pd.isna(lon): continue

            processed_data.append({
                "id": str(uuid.uuid4()),
                "name": row.get("名称") or row.get("施設名"),
                "address": find_address(row),
                "latitude": float(lat),
                "longitude": float(lon),
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
    print("新宿区のデータを取得します...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(SHINJUKU_CSV_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        df = None
        # 試行する文字コードと区切り文字
        encodings_to_try = ['utf-8', 'utf-8-sig', 'utf-16', 'cp932']
        separators_to_try = [',', '\t']

        for encoding in encodings_to_try:
            try:
                # 先に文字列としてデコードしてしまう（ここでエラーを無視できる）
                decoded_content = response.content.decode(encoding, errors='replace')
                for sep in separators_to_try:
                    try:
                        # デコード済みの文字列をCSVとして読み込む
                        df_temp = pd.read_csv(io.StringIO(decoded_content), sep=sep)
                        if '緯度' in df_temp.columns:
                            df = df_temp
                            # print(f"DEBUG: 新宿区読み込み成功 ({encoding}, '{sep}')")
                            break
                    except: continue
                if df is not None: break
            except: continue
        
        if df is None:
             print("エラー: 新宿区のCSVを読み込めませんでした。")
             return []

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')): continue

            processed_data.append({
                "id": str(uuid.uuid4()),
                "name": row.get("名称"),
                "address": find_address(row),
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

def get_nakano_data():
    print("中野区のデータを取得します...")
    try:
        response = requests.get(NAKANO_CSV_URL)
        response.raise_for_status()
        df = None
        for encoding in ['cp932', 'utf-8', 'utf-8-sig']:
            try:
                df_temp = pd.read_csv(io.BytesIO(response.content), encoding=encoding)
                if '緯度' in df_temp.columns:
                    df = df_temp
                    break
            except: pass
        if df is None: return []

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')): continue
            def is_available(val): return str(val).strip() in ['あり', '1', '○', 'TRUE', 'True']
            address = find_address(row)
            if address and not str(address).startswith("東京都"):
                address = f"東京都{address}"
            processed_data.append({
                "id": str(uuid.uuid4()),
                "name": row.get("名称"),
                "address": address,
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

def get_chuo_data():
    print("中央区のデータを取得します...")
    try:
        response = requests.get(CHUO_CSV_URL)
        response.raise_for_status()
        df = None
        for encoding in ['utf-8', 'cp932', 'utf-8-sig']:
            try:
                df_temp = pd.read_csv(io.BytesIO(response.content), encoding=encoding)
                if '緯度' in df_temp.columns:
                    df = df_temp
                    break
            except: pass
        if df is None: return []

        processed_data = []
        for _, row in df.iterrows():
            if pd.isna(row.get('緯度')) or pd.isna(row.get('経度')): continue
            def is_available(val): return str(val).strip() in ['有', 'あり', '○']
            start = row.get('利用開始時間')
            end = row.get('利用終了時間')
            opening_hours = f"{start}〜{end}" if pd.notna(start) and pd.notna(end) else None
            processed_data.append({
                "id": str(uuid.uuid4()),
                "name": row.get("名称"),
                "address": find_address(row),
                "latitude": float(row.get("緯度")),
                "longitude": float(row.get("経度")),
                "opening_hours": opening_hours,
                "availability_notes": row.get("備考") if pd.notna(row.get("備考")) else None,
                "is_wheelchair_accessible": is_available(row.get("車椅子使用者用トイレ有無")),
                "has_diaper_changing_station": is_available(row.get("乳幼児用設備設置トイレ有無")),
                "is_ostomate_accessible": is_available(row.get("オストメイト設置トイレ有無")),
                "is_station_toilet": False,
                "inside_gate": False,
                "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            })
        print(f"中央区: {len(processed_data)} 件取得しました。")
        return processed_data
    except Exception as e:
        print(f"中央区データの取得に失敗しました: {e}")
        return []

def get_station_doors_data():
    print(f"駅ドアデータ ({STATION_DOORS_CSV}) を読み込みます...")
    try:
        df = pd.read_csv(STATION_DOORS_CSV, encoding='utf-8')
        required_cols = ['station_name', 'line_name', 'car_number', 'nearest_toilet_id']
        if not all(col in df.columns for col in required_cols):
             print(f"エラー: {STATION_DOORS_CSV} に必要なカラムが不足しています。")
             return []
        return df.where(pd.notnull(df), None).to_dict('records')
    except FileNotFoundError:
        print(f"スキップ: {STATION_DOORS_CSV} が見つかりません。")
        return []
    except Exception as e:
        print(f"駅ドアデータの読み込みに失敗しました: {e}")
        return []

# -----------------------------------------------------------------
# 3. Supabase更新関数
# -----------------------------------------------------------------
def update_supabase(toilet_data, door_data):
    if not toilet_data and not door_data:
        print("更新対象のデータがありません。")
        return
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        print("既存の駅ドアデータを削除しています...")
        supabase.table(TABLE_NAME_DOORS).delete().neq('station_name', '_DUMMY_').execute()

        print("既存のトイレデータを削除しています...")
        supabase.table(TABLE_NAME_TOILETS).delete().neq('name', '_DUMMY_').execute()

        print(f"トイレデータ {len(toilet_data)} 件を挿入します...")
        CHUNK_SIZE = 500 
        for i in range(0, len(toilet_data), CHUNK_SIZE):
            chunk = toilet_data[i:i + CHUNK_SIZE]
            supabase.table(TABLE_NAME_TOILETS).insert(chunk).execute()
            print(f"  ... {min(i + CHUNK_SIZE, len(toilet_data))} / {len(toilet_data)} 件 完了")

        if door_data:
            print(f"駅ドアデータ {len(door_data)} 件を挿入します...")
            for i in range(0, len(door_data), CHUNK_SIZE):
                chunk = door_data[i:i + CHUNK_SIZE]
                supabase.table(TABLE_NAME_DOORS).insert(chunk).execute()
                print(f"  ... {min(i + CHUNK_SIZE, len(door_data))} / {len(door_data)} 件 完了")

        print("\nデータの同期が正常に完了しました！")
    except Exception as e:
        print(f"\nエラー(Supabase): {e}")

# -----------------------------------------------------------------
# 4. メイン実行処理
# -----------------------------------------------------------------
def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("エラー: 環境変数が設定されていません。")
        return

    print("=== データ同期バッチを開始します ===")
    start_time = time.time()

    all_toilets = []
    all_toilets.extend(get_sumida_data())
    all_toilets.extend(get_shinjuku_data())
    all_toilets.extend(get_nakano_data())
    all_toilets.extend(get_chuo_data())
    all_toilets.extend(get_station_data_from_csv())

    all_doors = get_station_doors_data()

    print(f"\n収集結果: トイレ {len(all_toilets)} 件, 駅ドア {len(all_doors)} 件")
    
    update_supabase(all_toilets, all_doors)

    print(f"=== 処理完了 (所要時間: {time.time() - start_time:.2f}秒) ===")

if __name__ == "__main__":
    main()