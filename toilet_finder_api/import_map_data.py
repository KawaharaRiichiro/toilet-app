import pandas as pd
import os
import hashlib

# 設定
INPUT_MAP_CSV = 'station_toilet_raw.csv'  
MASTER_TOILET_CSV = 'station_toilet.csv'   
TARGET_STRATEGIES_CSV = 'data/strategies.csv'

def clean_line_name(name):
    name = str(name)
    for removal in ['JR', '東京メトロ', '都営地下鉄']:
        name = name.replace(removal, '')
    return name

def generate_toilet_id(station_name, description):
    seed = f"{station_name}_{description}"
    return "T" + hashlib.md5(seed.encode()).hexdigest()[:8]

def main():
    if not os.path.exists(INPUT_MAP_CSV) or not os.path.exists(MASTER_TOILET_CSV):
        print("必要なファイルが足りません。")
        return

    df_raw = pd.read_csv(INPUT_MAP_CSV).fillna('')
    df_master = pd.read_csv(MASTER_TOILET_CSV).fillna('')
    df_strategies = pd.read_csv(TARGET_STRATEGIES_CSV).fillna('') if os.path.exists(TARGET_STRATEGIES_CSV) else pd.DataFrame()

    new_master_rows = []
    new_strategy_rows = []

    # 既存の「駅名 + 説明」のセットをリスト化（IDが変わっていても名称でブロックするため）
    existing_combinations = set(zip(df_master['station_name'], df_master['description']))

    for _, row in df_raw.iterrows():
        station = row['station_name']
        desc = row.get('name', f"{station}付近のトイレ")
        t_id = row['id'] if 'id' in row and row['id'] else generate_toilet_id(station, desc)

        # 【強化された重複判定】
        # 1. IDが既に存在するか？
        # 2. あるいは、同じ駅に同じ説明のトイレが既に存在するか？
        is_duplicate = (t_id in df_master['toilet_id'].values) or ((station, desc) in existing_combinations)

        if not is_duplicate:
            # マスタへの追加処理（省略せず以前のロジックを維持）
            features = []
            if row.get('wheelchair') == '○': features.append("wheelchair")
            # ... (中略: features作成ロジック) ...
            
            new_master_rows.append({
                'toilet_id': t_id,
                'station_name': station,
                'floor': '不明',
                'lat': row.get('lat', 0.0),
                'lon': row.get('lon', 0.0),
                'description': desc,
                'features': ",".join(features)
            })

            # 攻略データへの追加
            new_strategy_rows.append({
                'line_name': clean_line_name(row.get('line_name', '不明')),
                'station_name': station,
                'direction': 1,
                'car_pos': 0.0,
                'facility': '調査中',
                'available_time': 'ALL',
                'crowd': 3,
                'target_toilet_id': t_id,
                'route_memo': '新規インポート'
            })

    # (以下、ファイル保存処理 ... 前回同様)
    if new_master_rows:
        pd.concat([df_master, pd.DataFrame(new_master_rows)], ignore_index=True).to_csv(MASTER_TOILET_CSV, index=False)
        print(f"{len(new_master_rows)}件追加しました。")

if __name__ == '__main__':
    main()