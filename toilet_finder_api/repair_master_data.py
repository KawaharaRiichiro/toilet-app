import pandas as pd
import hashlib
import os

# ファイルパス
STRATEGIES_CSV = 'data/strategies.csv'
MASTER_CSV = 'station_toilet.csv'
# もし以前のバックアップやOSM由来のファイルがあれば、そこから座標を復元します
ORIGINAL_OSM_CSV = 'station_toilet_raw.csv' 

def repair():
    print("--- 最終データ復元・修復フェーズ ---")
    
    if not os.path.exists(STRATEGIES_CSV):
        print(f"エラー: {STRATEGIES_CSV} が見つかりません。")
        return

    # 1. 現在の攻略データ（IDの正解）を読み込む
    df_str = pd.read_csv(STRATEGIES_CSV, dtype=str).fillna('')
    
    # 2. 座標ソースの準備
    # 以前アップロードされた座標入りの生データがあれば読み込む
    coords_map = {}
    if os.path.exists(ORIGINAL_OSM_CSV):
        print(f"情報: {ORIGINAL_OSM_CSV} から座標を復元します...")
        df_raw = pd.read_csv(ORIGINAL_OSM_CSV, dtype=str).fillna('')
        for _, r in df_raw.iterrows():
            # 駅名と名称（description）をキーにして座標を保持
            key = f"{r['station_name']}_{r.get('name', r.get('description', ''))}"
            coords_map[key] = (r.get('lat', '0.0'), r.get('lon', '0.0'))
    
    # 3. マスタの再構築
    new_master_data = []
    processed_ids = set()

    print("マスタデータの属性をクリーンアップ中...")
    
    for _, row in df_str.iterrows():
        t_id = row['target_toilet_id']
        station = row['station_name']
        memo = row['route_memo']
        
        if t_id not in processed_ids:
            # 座標の復元を試みる
            key = f"{station}_{memo}"
            lat, lon = coords_map.get(key, ('0.0', '0.0'))
            
            # 階数の推測（メモから）
            floor = '不明'
            if '1階' in memo or '1F' in memo: floor = '1F'
            elif 'B1' in memo or '地下1階' in memo: floor = 'B1F'

            new_master_data.append({
                'toilet_id': t_id,
                'station_name': station,
                'floor': floor,
                'lat': lat,
                'lon': lon,
                'description': memo,
                'features': ''
            })
            processed_ids.add(t_id)

    # 4. 保存
    df_new_master = pd.DataFrame(new_master_data)
    df_new_master.to_csv(MASTER_CSV, index=False, encoding='utf-8')
    
    print("-" * 30)
    print(f"完了: {MASTER_CSV} を {len(df_new_master)} 件で更新しました。")
    print(f"座標復元成功: {len([x for x in new_master_data if x['lat'] != '0.0'])} 件")
    print("この後、generate_sql.py を実行して Supabase のデータを最新化してください。")

if __name__ == "__main__":
    repair()