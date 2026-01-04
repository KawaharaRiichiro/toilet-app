import pandas as pd
import os

# ファイルパス設定
MASTER_CSV = 'station_toilet.csv'      # 現在のマスタ（これを更新する）
RAW_OSM_CSV = 'station_toilet_raw.csv' # 座標が入っている元の生データ

def update_coordinates():
    print("--- 座標アップデート・データ整合性チェック ---")
    
    if not os.path.exists(MASTER_CSV) or not os.path.exists(RAW_OSM_CSV):
        print("エラー: 必要なCSVファイルが見つかりません。")
        return

    # 1. データの読み込み
    df_master = pd.read_csv(MASTER_CSV, dtype=str).fillna('')
    df_raw = pd.read_csv(RAW_OSM_CSV, dtype=str).fillna('')

    print(f"読み込み: マスタ {len(df_master)}件 / ソースデータ {len(df_raw)}件")

    # 2. 座標情報の紐付け辞書を作成
    raw_coords_lookup = {}
    for _, row in df_raw.iterrows():
        # 駅名 + 名称、または駅名のみでマッチングするためのキー
        s_name = str(row['station_name']).strip()
        t_name = str(row.get('name', row.get('description', ''))).strip()
        raw_coords_lookup[f"{s_name}_{t_name}"] = (row.get('lat', '0.0'), row.get('lon', '0.0'))

    # 3. マスタの座標を更新
    update_count = 0
    zero_count = 0
    
    for idx, row in df_master.iterrows():
        s_name = str(row['station_name']).strip()
        desc = str(row['description']).strip()
        
        # マッチング試行1: 駅名 + 説明
        key = f"{s_name}_{desc}"
        found_coords = raw_coords_lookup.get(key)
        
        # マッチング試行2: 駅名が一致する最初の1件（フォールバック）
        if not found_coords or found_coords[0] == '0.0':
            station_matches = df_raw[df_raw['station_name'] == s_name]
            if not station_matches.empty:
                # 0.0以外の座標を持っているものを優先的に探す
                valid_coords = station_matches[station_matches['lat'] != '0.0']
                if not valid_coords.empty:
                    found_coords = (valid_coords.iloc[0]['lat'], valid_coords.iloc[0]['lon'])
                else:
                    found_coords = (station_matches.iloc[0]['lat'], station_matches.iloc[0]['lon'])

        if found_coords:
            df_master.at[idx, 'lat'] = found_coords[0]
            df_master.at[idx, 'lon'] = found_coords[1]
            if found_coords[0] != '0.0':
                update_count += 1
            else:
                zero_count += 1

    # 4. 保存
    df_master.to_csv(MASTER_CSV, index=False, encoding='utf-8')
    
    print("-" * 30)
    print(f"結果報告:")
    print(f"  - 有効な座標(0.0以外)に更新された件数: {update_count} 件")
    print(f"  - 依然として 0.0 のままの件数: {zero_count} 件")
    
    if update_count == 0:
        print("\n[警告] 有効な座標が1件も取り込まれませんでした。")
        print(f"ソースファイル '{RAW_OSM_CSV}' の lat/lon カラムが 0.0 ばかりになっていないか確認してください。")

if __name__ == "__main__":
    update_coordinates()