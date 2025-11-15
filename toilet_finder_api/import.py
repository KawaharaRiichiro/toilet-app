import os
import requests
import pandas as pd
import io
import uuid
import time
import re
from supabase import create_client, Client
from dotenv import load_dotenv
from station_data_importer import get_station_data_from_csv

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# -----------------------------------------------------------------
# 1. 設定
# -----------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME_TOILETS = 'toilets'
TABLE_NAME_DOORS = 'station_platform_doors'

# レガシー関数用URL
SHINJUKU_CSV_URL = "https://www.city.shinjuku.lg.jp/content/000399974.csv"
NAKANO_CSV_URL = "https://www2.wagmap.jp/nakanodatamap/nakanodatamap/opendatafile/map_50/CSV/opendata_550070.csv"
CHUO_CSV_URL = "https://www.city.chuo.lg.jp/documents/984/kousyuutoilet.csv"

STATION_DOORS_CSV = "station_doors.csv"

# -----------------------------------------------------------------
# 2. 区ごとのデータ設定リスト (WARD_CONFIGS)
# -----------------------------------------------------------------
WARD_CONFIGS = [
    # 墨田区
    {
        "name": "墨田区",
        "url": "https://www.opendata.metro.tokyo.lg.jp/sumida/131075_public_toilet.csv",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度", "lat"],
            "lon": ["経度", "lon"],
            "address": ["所在地_連結表記", "所在地", "住所", "施設所在地"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす使用者用トイレ"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーシート", "ベビーベッド"],
            "ostomate": ["オストメイト設置トイレ有無", "オストメイト"]
        }
    },
    # 港区
    {
        "name": "港区",
        "url": "https://opendata.city.minato.tokyo.jp/dataset/40418c19-d531-4c1e-bebd-46784f9092dc/resource/13187d80-4be8-4597-b338-c79d13f2a924/download/koshubenjoichiran.csv",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度", "lat"],
            "lon": ["経度", "lon"],
            "address": ["所在地", "住所", "施設所在地"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす対応", "車いす"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーベッド", "ベビーシート"],
            "ostomate": ["オストメイト設置トイレ有無", "オストメイト"]
        }
    },
    # 板橋区
    {
        "name": "板橋区",
        "url": "https://www.opendata.metro.tokyo.lg.jp/itabashi/131199_public_toilet.csv",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地_連結表記", "所在地", "住所", "施設所在地"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーシート", "ベビーベッド"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
    # 台東区
    {
        "name": "台東区",
        "url": "https://www.city.taito.lg.jp/kusei/online/opendata/seikatu/shisethutizujouhou.files/20250314_koshu_koen_toilet.csv", 
        "mapping": {
            "name": ["名称"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地_連結表記", "所在地", "住所"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーシート"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
     # 豊島区
    {
        "name": "豊島区",
        "url": "https://www.opendata.metro.tokyo.lg.jp/toyoshima/R4_public_toilet.csv",
        "mapping": {
            "name": ["名称"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地", "住所"],
            "wheelchair": ["車椅子使用者用トイレ有無"],
            "baby": ["乳幼児用設備設置トイレ有無"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
    # 品川区
    {
        "name": "品川区",
        "url": "http://www.city.shinagawa.tokyo.jp/ct/other000081600/toilet.csv",
        "mapping": {
            "name": ["施設名", "名称"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["住所"],
            "wheelchair": ["バリアフリートイレ数", "車椅子使用者用トイレ有無"],
            "baby": ["ベビーベッド( 有、無)", "乳幼児用設備設置トイレ有無"],
            "ostomate": ["オストメイト(有、無)", "オストメイト設置トイレ有無"]
        }
    },
   # 江戸川区
    {
        "name": "江戸川区",
        "url": "https://www.opendata.metro.tokyo.lg.jp/edogawa/131237_public_toilet.csv",
        "mapping": {
            "name": ["名称"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地_連結表記", "所在地", "住所"],
            "wheelchair": ["車椅子使用者用トイレ有無"],
            "baby": ["乳幼児用設備設置トイレ有無"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
  # 目黒区
    {
        "name": "目黒区",
        "url": "https://data.bodik.jp/dataset/73861054-d37f-4d84-a7ac-7d1010aae790/resource/79060cab-e0e4-468b-bac6-b82d4610df47/download/131105_public_toilet_20210401.csv",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地", "住所"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす対応"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーチェア", "ベビーベッド"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
    # 江東区
    {
        "name": "江東区",
        "url": "https://www.opendata.metro.tokyo.lg.jp/koto/131083_013_public_toilet.csv",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地_連結表記", "所在地", "住所", "施設所在地"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす対応"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーチェア", "ベビーベッド"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
    # 荒川区
    {
        "name": "荒川区",
        "url": "https://www.city.arakawa.tokyo.jp/documents/23112/131181_public_toilet.csv",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地_連結表記", "所在地", "住所", "施設所在地"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす対応"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーチェア", "ベビーベッド"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
    # 足立区
    {
        "name": "足立区",
        "url": "https://www.city.adachi.tokyo.jp/documents/61022/04kousyuutoireitirann_20250401.csv",
        "mapping": {
            "name": ["公衆トイレ名", "名称", "施設名"],
            "lat": ["緯度"], 
            "lon": ["経度"],
            "address": ["住所", "所在地", "所在地_連結表記"],
            "wheelchair": ["車椅子使用者用トイレ有無"],
            "baby": ["乳幼児用設備設置トイレ有無"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
    # 葛飾区
    {
        "name": "葛飾区",
        "url": "https://www.opendata.metro.tokyo.lg.jp/katsushika/131229_public_toilet.csv",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地_連結表記", "所在地", "住所", "施設所在地"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす対応"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーチェア", "ベビーベッド"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
    # 西東京市
    {
        "name": "西東京市",
        "url": "https://www.opendata.metro.tokyo.lg.jp/nishitokyo/132292_public_toilet.xlsx",
        "mapping": {
            "name": ["名称", "施設名"],
            "lat": ["緯度"],
            "lon": ["経度"],
            "address": ["所在地_連結表記", "所在地", "住所", "施設所在地"],
            "wheelchair": ["車椅子使用者用トイレ有無", "車いす対応"],
            "baby": ["乳幼児用設備設置トイレ有無", "ベビーチェア", "ベビーベッド"],
            "ostomate": ["オストメイト設置トイレ有無"]
        }
    },
]

# -----------------------------------------------------------------
# 3. データ取得関数群
# -----------------------------------------------------------------

geolocator = Nominatim(user_agent="tokyo_toilet_map_v6_adachi_fix", timeout=30)

geocode_with_delay = RateLimiter(
    geolocator.geocode, 
    min_delay_seconds=2.0, 
    max_retries=3, 
    error_wait_seconds=10.0, 
    swallow_exceptions=True
)

# 【重要】漢数字をアラビア数字に変換する関数（足立区対策）
def normalize_jp_address(text):
    if not isinstance(text, str): return str(text)
    kanji_map = str.maketrans({
        '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
        '六': '6', '七': '7', '八': '8', '九': '9', '〇': '0'
    })
    text = text.translate(kanji_map)
    # 「丁目」「番地」「番」「号」などをハイフンに
    text = re.sub(r'丁目|番地|番|号', '-', text)
    # 末尾のハイフン削除
    text = text.rstrip('-')
    return text

def get_coords_from_address(ward_name, address):
    if not address: return None, None
    
    # 1. そのまま検索
    search_addr_1 = str(address)
    if ward_name not in search_addr_1:
        search_addr_1 = f"{ward_name}{search_addr_1}"
    
    query_1 = search_addr_1 if "東京都" in search_addr_1 else f"東京都{search_addr_1}"
    try:
        loc = geocode_with_delay(query_1)
        if loc: return loc.latitude, loc.longitude
    except: pass
    
    # 2. 正規化して検索 (足立区はここでヒットするはず)
    normalized_addr = normalize_jp_address(str(address))
    search_addr_2 = normalized_addr
    if ward_name not in search_addr_2:
        search_addr_2 = f"{ward_name}{search_addr_2}"
    
    query_2 = search_addr_2 if "東京都" in search_addr_2 else f"東京都{search_addr_2}"
    
    try:
        # print(f"    (再試行: {query_2})") # デバッグ用
        loc = geocode_with_delay(query_2)
        if loc: return loc.latitude, loc.longitude
    except: pass

    return None, None

def find_col_name(df, candidates):
    if not candidates: return None
    # 列名の空白除去して比較
    normalized_cols = {str(c).strip(): c for c in df.columns}
    for cand in candidates:
        if cand in normalized_cols:
            return normalized_cols[cand]
    return None

def find_value_by_keys(row, keys):
    if not keys: return None
    for key in keys:
        if key in row and pd.notna(row[key]):
            return row[key]
    return None

def fetch_general_csv_data(config):
    ward_name = config["name"]
    url = config["url"]
    mapping = config["mapping"]
    
    print(f"■ {ward_name} のデータを取得中...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        df = None
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if url.lower().endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(io.BytesIO(response.content))
            except ImportError:
                print("  [Error] 'pip install openpyxl' が必要です。")
                return []
            except: return []
        else:
            for encoding in ['utf-8', 'cp932', 'shift_jis', 'utf-8-sig']:
                for header_row in [0, 1, 2, 3]: 
                    try:
                        df_temp = pd.read_csv(io.BytesIO(response.content), encoding=encoding, header=header_row)
                        df_temp.columns = df_temp.columns.astype(str).str.strip()
                        
                        has_lat = find_col_name(df_temp, mapping["lat"])
                        has_addr = find_col_name(df_temp, mapping["address"])
                        
                        if has_lat or has_addr:
                            df = df_temp
                            break
                    except: continue
                if df is not None: break

        if df is None:
             print(f"  [Error] {ward_name}: ファイルの読み込みに失敗しました。")
             return []

        processed_data = []
        geo_wait_count = 0

        lat_col = find_col_name(df, mapping["lat"])
        lon_col = find_col_name(df, mapping["lon"])
        name_col = find_col_name(df, mapping["name"])
        addr_col = find_col_name(df, mapping["address"])
        
        wheel_cols = mapping.get("wheelchair", [])
        baby_cols = mapping.get("baby", [])
        osto_cols = mapping.get("ostomate", [])

        for _, row in df.iterrows():
            name = row[name_col] if name_col and name_col in row else f"{ward_name}の公衆トイレ"
            address = row[addr_col] if addr_col and addr_col in row else None

            lat, lon = None, None
            if lat_col and lon_col and lat_col in row and lon_col in row:
                lat = row[lat_col]
                lon = row[lon_col]

            if (pd.isna(lat) or pd.isna(lon)) and address:
                if geo_wait_count == 0:
                    print(f"    [注意] '{ward_name}' は緯度経度がありません。住所から場所を検索します（時間がかかります）...")
                
                geo_wait_count += 1
                if geo_wait_count % 10 == 0: print(f"    ... {geo_wait_count} 件目を検索中")
                
                lat, lon = get_coords_from_address(ward_name, address)

            elif (pd.isna(address) or address is None) and lat and lon:
                address = f"東京都{ward_name}"

            if pd.isna(lat) or pd.isna(lon) or lat is None or lon is None:
                continue

            def get_avail(cols):
                real_col = find_col_name(df, cols)
                if not real_col or real_col not in row: return False
                val = row[real_col]
                if pd.isna(val): return False
                s = str(val).strip()
                if s in ['○', '有', 'あり', 'TRUE', 'True', 'true', 'yes', '1', '1.0']: return True
                try:
                    if float(s) > 0: return True
                except ValueError: pass
                return False

            wheelchair = get_avail(wheel_cols)
            baby = get_avail(baby_cols)
            ostomate = get_avail(osto_cols)

            # ID固定化
            unique_string = f"{ward_name}_{name}_{address}"
            fixed_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))

            processed_data.append({
                "id": fixed_id, 
                "name": name,
                "address": address,
                "latitude": float(lat),
                "longitude": float(lon),
                "opening_hours": find_value_by_keys(row, ["供用時間", "利用時間", "利用開始時間", "利用可能時間OPENS"]), 
                "availability_notes": find_value_by_keys(row, ["備考", "特記事項", "利用可能時間特記事項"]),
                "is_wheelchair_accessible": wheelchair,
                "has_diaper_changing_station": baby,
                "is_ostomate_accessible": ostomate,
                "is_station_toilet": False,
                "inside_gate": False,
                "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "average_rating": 0.0,
                "review_count": 0,
                "last_synced_at": time.strftime('%Y-%m-%dT%H:%M:%SZ')
            })
        print(f"  -> {ward_name}: {len(processed_data)} 件取得しました。")
        return processed_data

    except Exception as e:
        print(f"  -> {ward_name} データの取得に失敗しました: {e}")
        return []

def get_shinjuku_data():
    # (省略: 元のまま)
    print("新宿区のデータを取得します(Legacy)...")
    # ... (元のコード) ...
    return [] # 省略していますが、元のファイルの中身は残しておいてください

def get_nakano_data():
    # (省略: 元のまま)
    return []

def get_chuo_data():
    # (省略: 元のまま)
    return []

def get_station_doors_data():
    print(f"駅ドアデータ ({STATION_DOORS_CSV}) を読み込みます...")
    try:
        df = pd.read_csv(STATION_DOORS_CSV, encoding='utf-8')
        # ID紐付け解除コードは削除済み
        return df.where(pd.notnull(df), None).to_dict('records')
    except: return []

# -----------------------------------------------------------------
# 4. Supabase更新関数
# -----------------------------------------------------------------
def update_supabase(toilet_data, door_data):
    if not toilet_data:
        print("更新対象のデータがありません。")
        return
    try:
        # 重複排除（重要）
        unique_toilets = {t['id']: t for t in toilet_data}.values()
        clean_toilet_data = list(unique_toilets)
        print(f"重複削除後: {len(toilet_data)} -> {len(clean_toilet_data)} 件")

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        print("既存データを削除中...")
        supabase.table(TABLE_NAME_DOORS).delete().neq('station_name', '_DUMMY_').execute()
        supabase.table(TABLE_NAME_TOILETS).delete().neq('name', '_DUMMY_').execute()

        print(f"トイレデータ {len(clean_toilet_data)} 件を挿入します...")
        CHUNK_SIZE = 500 
        for i in range(0, len(clean_toilet_data), CHUNK_SIZE):
            chunk = clean_toilet_data[i:i + CHUNK_SIZE]
            supabase.table(TABLE_NAME_TOILETS).insert(chunk).execute()
            print(f"  ... {min(i + CHUNK_SIZE, len(clean_toilet_data))} / {len(clean_toilet_data)} 件")

        if door_data:
            print(f"駅ドアデータ {len(door_data)} 件を挿入します...")
            for i in range(0, len(door_data), CHUNK_SIZE):
                chunk = door_data[i:i + CHUNK_SIZE]
                try:
                    supabase.table(TABLE_NAME_DOORS).insert(chunk).execute()
                    print(f"  ... {min(i + CHUNK_SIZE, len(door_data))} / {len(door_data)} 件")
                except Exception as e_door:
                    print(f"  [Warning] ドアデータ挿入エラー: {e_door}")
                    print("  (station_doors.csv のIDが一致していない可能性があります)")

        print("\n同期完了！")
    except Exception as e:
        print(f"\nエラー(Supabase): {e}")

# -----------------------------------------------------------------
# 5. メイン実行処理
# -----------------------------------------------------------------
def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("エラー: 環境変数が設定されていません。")
        return

    print("=== データ同期バッチを開始します ===")
    start_time = time.time()

    all_toilets = []
    
    for config in WARD_CONFIGS:
        all_toilets.extend(fetch_general_csv_data(config))

    # レガシー関数の呼び出しも忘れずに（コード省略時は注意）
    # all_toilets.extend(get_shinjuku_data()) 
    # ...

    all_toilets.extend(get_station_data_from_csv())

    all_doors = get_station_doors_data()

    print(f"\n収集結果: トイレ {len(all_toilets)} 件, 駅ドア {len(all_doors)} 件")
    
    update_supabase(all_toilets, all_doors)

    print(f"=== 処理完了 (所要時間: {time.time() - start_time:.2f}秒) ===")

if __name__ == "__main__":
    main()