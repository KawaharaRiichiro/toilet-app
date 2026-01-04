import pandas as pd
import os
import uuid
import re

# ファイルパス定義
STATIONS_CSV = 'data/stations.csv'
STRATEGIES_CSV = 'data/strategies.csv'
# TOILET_MASTER_CSV = 'station_toilet.csv' # 廃止

# 出力ファイル設定
OUTPUT_SQL_1 = '01_schema.sql'     # テーブル定義
OUTPUT_SQL_2 = '02_stations.sql'   # 駅・路線データ
OUTPUT_SQL_3_PREFIX = '03_strategies'

# 分割設定
MAX_INSERTS_PER_FILE = 500

# ---------------------------------------------------------
# 路線ごとのホーム規則定義
# ---------------------------------------------------------
PLATFORM_RULES = {
    "銀座線": {1: "1番線", -1: "2番線"},
    "丸ノ内線": {1: "1番線", -1: "2番線"},
    "日比谷線": {1: "1番線", -1: "2番線"},
    "東西線": {1: "1番線", -1: "2番線"},
    "千代田線": {1: "1番線", -1: "2番線"},
    "有楽町線": {1: "1番線", -1: "2番線"},
    "半蔵門線": {1: "1番線", -1: "2番線"},
    "南北線": {1: "1番線", -1: "2番線"},
    "副都心線": {1: "1番線", -1: "2番線"},
    "都営浅草線": {1: "1番線", -1: "2番線"},
    "都営三田線": {1: "1番線", -1: "2番線"},
    "都営新宿線": {1: "1番線", -1: "2番線"},
    "都営大江戸線": {1: "1番線", -1: "2番線"},
    "山手線": {1: "内回りホーム", -1: "外回りホーム"}, 
    "京浜東北線": {1: "1番線", -1: "2番線"},
    "中央線": {1: "1番線", -1: "2番線"},
    "総武線": {1: "1番線", -1: "2番線"},
    "小田急小田原線": {1: "1番線", -1: "2番線"},
    "東急東横線": {1: "1番線", -1: "2番線"},
}

def normalize_line_name(name: str) -> str:
    if not name: return ""
    normalized = str(name).strip()
    prefixes = ["東京メトロ", "都営地下鉄", "都営", "JR", "東急", "小田急", "京王", "西武", "東武", "京急"]
    for p in prefixes:
        normalized = normalized.replace(p, "")
    if normalized.endswith("線"): normalized = normalized[:-1]
    elif normalized.endswith("ライン"): normalized = normalized.replace("ライン", "")
    return normalized.strip()

def get_platform_name_from_rules(line_name, direction):
    norm_target = normalize_line_name(line_name)
    for key in PLATFORM_RULES:
        norm_key = normalize_line_name(key)
        if norm_key in norm_target or norm_target in norm_key:
            return PLATFORM_RULES[key].get(direction, "ホーム")
    return "ホーム"

def load_csv_safe(filepath):
    if not os.path.exists(filepath): return pd.DataFrame()
    try:
        df = pd.read_csv(filepath, dtype=str, encoding='utf-8-sig').fillna('')
        df.columns = df.columns.str.strip()
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(filepath, dtype=str, encoding='cp932').fillna('')
            df.columns = df.columns.str.strip()
            return df
        except: return pd.DataFrame()
    except: return pd.DataFrame()

def save_sql_split(sql_statements, base_filename, max_lines=MAX_INSERTS_PER_FILE):
    if not sql_statements: return
    total_parts = (len(sql_statements) // max_lines) + 1
    for i in range(total_parts):
        start_idx = i * max_lines
        end_idx = start_idx + max_lines
        chunk = sql_statements[start_idx:end_idx]
        if not chunk: continue
        filename = f"{base_filename}_part{i+1}.sql"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(chunk))
        print(f"  -> {filename} を生成しました ({len(chunk)}行)")

def generate_sql():
    print("CSVファイルを読み込んでいます...")
    df_st = load_csv_safe(STATIONS_CSV)
    df_str = load_csv_safe(STRATEGIES_CSV) # 手動データのみ

    if df_st.empty:
        print(f"エラー: {STATIONS_CSV} が読み込めないか、空です。")
        return

    if 'station_order' in df_st.columns:
        df_st['station_order_int'] = pd.to_numeric(df_st['station_order'], errors='coerce').fillna(0).astype(int)

    # 1. スキーマ定義
    sql_1 = [
        "DROP TABLE IF EXISTS toilet_strategies CASCADE;",
        "DROP TABLE IF EXISTS toilets CASCADE;",
        "DROP TABLE IF EXISTS line_stations CASCADE;",
        "DROP TABLE IF EXISTS stations CASCADE;",
        "DROP TABLE IF EXISTS lines CASCADE;",
        "",
        "CREATE TABLE public.lines (id uuid NOT NULL DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE, color text, max_cars integer DEFAULT 10, PRIMARY KEY (id));",
        "CREATE TABLE public.stations (id uuid NOT NULL DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE, lat double precision, lng double precision, PRIMARY KEY (id));",
        """CREATE TABLE public.line_stations (
        line_id uuid REFERENCES public.lines(id) ON DELETE CASCADE,
        station_id uuid REFERENCES public.stations(id) ON DELETE CASCADE,
        station_order integer,
        dir_1_label text, dir_m1_label text,
        dir_1_next_station_id uuid REFERENCES public.stations(id),
        dir_1_next_next_station_id uuid REFERENCES public.stations(id),
        dir_m1_next_station_id uuid REFERENCES public.stations(id),
        dir_m1_next_next_station_id uuid REFERENCES public.stations(id),
        PRIMARY KEY (line_id, station_id));""",
        """CREATE TABLE public.toilets (
        id text NOT NULL, station_name text, floor text, lat double precision, lng double precision, description text, features text, PRIMARY KEY (id));""",
        """CREATE TABLE public.toilet_strategies (
        id uuid NOT NULL DEFAULT gen_random_uuid(), line_name text, station_id uuid REFERENCES public.stations(id) ON DELETE CASCADE,
        direction integer, platform_name text, car_pos double precision, facility_type text, available_time text,
        crowd_level integer, target_toilet_id text, route_memo text, PRIMARY KEY (id));""",
        "ALTER TABLE public.lines DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.stations DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.line_stations DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.toilets DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.toilet_strategies DISABLE ROW LEVEL SECURITY;"
    ]
    with open(OUTPUT_SQL_1, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_1))
    print(f"  -> {OUTPUT_SQL_1} を生成しました ({len(sql_1)}行)")

    # 2. 駅・路線データ
    sql_2 = []
    
    # lines
    line_map = {} 
    if 'line_name' in df_st.columns:
        unique_lines = df_st['line_name'].unique()
        for line in unique_lines:
            if not line: continue
            line_id = str(uuid.uuid4())
            line_map[line] = line_id
            
            # line_name に対応する行を取得
            line_rows = df_st[df_st['line_name'] == line]
            
            # color の取得
            color = '#808080'
            if not line_rows.empty:
                color = line_rows.iloc[0]['line_color']
            
            # max_cars の取得 (CSVから読み込む)
            max_cars = 10
            if 'max_cars' in df_st.columns and not line_rows.empty:
                try:
                    val = line_rows.iloc[0]['max_cars']
                    max_cars = int(val) if pd.notnull(val) and str(val).isdigit() else 10
                except:
                    max_cars = 10
            
            sql_2.append(f"INSERT INTO lines (id, name, color, max_cars) VALUES ('{line_id}', '{line}', '{color}', {max_cars}) ON CONFLICT (name) DO UPDATE SET color = EXCLUDED.color, max_cars = EXCLUDED.max_cars;")
    
    # stations
    station_map = {} 
    if 'station_name' in df_st.columns:
        for _, row in df_st.iterrows():
            s_name = row['station_name'].replace("'", "''")
            if not s_name: continue
            if s_name not in station_map:
                station_map[s_name] = str(uuid.uuid4())
            lat = row.get('lat', 'NULL')
            lng = row.get('lng', row.get('lon', 'NULL'))
            if not lat: lat = 'NULL'
            if not lng: lng = 'NULL'
            s_id = station_map[s_name]
            sql_2.append(f"INSERT INTO stations (id, name, lat, lng) VALUES ('{s_id}', '{s_name}', {lat}, {lng}) ON CONFLICT (name) DO UPDATE SET lat = EXCLUDED.lat, lng = EXCLUDED.lng;")
    
    # line_stations
    sql_2_ls = []
    if 'line_name' in df_st.columns and 'station_name' in df_st.columns:
        grouped = df_st.groupby('line_name')
        for line_name, group in grouped:
            if not line_name or line_name not in line_map:
                continue

            sorted_group = group.sort_values('station_order_int')
            if sorted_group.empty: continue
            
            order_to_id = {}
            for _, row in sorted_group.iterrows():
                s_name = row['station_name']
                s_id = station_map.get(s_name)
                order = int(row['station_order_int'])
                if s_id: order_to_id[order] = s_id

            first_st = sorted_group.iloc[0]['station_name']
            last_st = sorted_group.iloc[-1]['station_name']
            default_dir_1 = f"{last_st} 方面"
            default_dir_m1 = f"{first_st} 方面"

            for _, row in group.iterrows():
                l_id = line_map.get(line_name)
                s_id = station_map.get(row['station_name'])
                
                if not l_id or not s_id:
                    continue

                order = int(row['station_order_int'])
                d1 = row.get('dir_1_label', '')
                dm1 = row.get('dir_m1_label', '')
                d1_val = f"'{d1}'" if d1 else f"'{default_dir_1}'"
                dm1_val = f"'{dm1}'" if dm1 else f"'{default_dir_m1}'"

                next_1_id = order_to_id.get(order + 1, 'NULL')
                next_next_1_id = order_to_id.get(order + 2, 'NULL')
                next_m1_id = order_to_id.get(order - 1, 'NULL')
                next_next_m1_id = order_to_id.get(order - 2, 'NULL')
                
                v_next_1 = f"'{next_1_id}'" if next_1_id != 'NULL' else "NULL"
                v_next_next_1 = f"'{next_next_1_id}'" if next_next_1_id != 'NULL' else "NULL"
                v_next_m1 = f"'{next_m1_id}'" if next_m1_id != 'NULL' else "NULL"
                v_next_next_m1 = f"'{next_next_m1_id}'" if next_next_m1_id != 'NULL' else "NULL"

                sql_2_ls.append(
                    f"INSERT INTO line_stations (line_id, station_id, station_order, dir_1_label, dir_m1_label, dir_1_next_station_id, dir_1_next_next_station_id, dir_m1_next_station_id, dir_m1_next_next_station_id) "
                    f"VALUES ('{l_id}', '{s_id}', {order}, {d1_val}, {dm1_val}, {v_next_1}, {v_next_next_1}, {v_next_m1}, {v_next_next_m1}) "
                    f"ON CONFLICT (line_id, station_id) DO UPDATE SET dir_1_label = EXCLUDED.dir_1_label, dir_m1_label = EXCLUDED.dir_m1_label, dir_1_next_station_id = EXCLUDED.dir_1_next_station_id, dir_1_next_next_station_id = EXCLUDED.dir_1_next_next_station_id, dir_m1_next_station_id = EXCLUDED.dir_m1_next_station_id, dir_m1_next_next_station_id = EXCLUDED.dir_m1_next_next_station_id;"
                )

    with open(OUTPUT_SQL_2, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_2))
    print(f"  -> {OUTPUT_SQL_2} を生成しました ({len(sql_2)}行)")
    
    save_sql_split(sql_2_ls, '02_stations', max_lines=500)

    # 3. 攻略データ (strategies.csv のみ使用)
    sql_3 = []
    sql_3.append("-- 3. 攻略・トイレデータ登録 (strategies.csvベース)")
    
    # 登録済みトイレID管理用
    registered_toilet_ids = set()

    if not df_str.empty and 'line_name' in df_str.columns:
        for _, row in df_str.iterrows():
            line_name = row['line_name']
            s_name = row['station_name'].replace("'", "''")
            
            # toiletsテーブルへの登録
            # strategies.csv に target_toilet_id があればそれを使う、なければ新規UUID発行
            t_id = row.get('target_toilet_id', '')
            if not t_id or t_id == 'nan':
                t_id = str(uuid.uuid4())
            
            # 重複登録防止
            if t_id not in registered_toilet_ids:
                # 手動データには緯度経度や詳細がない場合が多いのでデフォルト値
                # 将来的にAIで生成したテキストを 'description' に入れるなどの拡張が可能
                desc = str(row.get('route_memo', row.get('note', ''))).replace("'", "''")
                sql_3.append(f"INSERT INTO toilets (id, station_name, floor, lat, lng, description, features) VALUES ('{t_id}', '{s_name}', '', NULL, NULL, '{desc}', '') ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;")
                registered_toilet_ids.add(t_id)

            # toilet_strategiesへの登録
            direction = int(row.get('direction', '1'))
            car_pos = row.get('car_pos', '0.0')
            fac = row.get('facility', '調査中')
            avail = row.get('available_time', 'ALL')
            crowd = row.get('crowd', '3')
            memo = str(row.get('route_memo', row.get('note', ''))).replace("'", "''")
            
            platform = row.get('platform_name', '')
            if not platform or str(platform) == 'nan':
                platform = get_platform_name_from_rules(line_name, direction)
            platform = str(platform).replace("'", "''")
            
            sql_3.append(
                f"INSERT INTO toilet_strategies (line_name, station_id, direction, platform_name, car_pos, facility_type, available_time, crowd_level, target_toilet_id, route_memo) "
                f"SELECT '{line_name}', id, {direction}, '{platform}', {car_pos}, '{fac}', '{avail}', {crowd}, '{t_id}', '{memo}' "
                f"FROM stations WHERE name = '{s_name}' LIMIT 1;"
            )

    save_sql_split(sql_3, OUTPUT_SQL_3_PREFIX)
    
    print("完了: SQLファイルを生成しました。")

if __name__ == '__main__':
    generate_sql()