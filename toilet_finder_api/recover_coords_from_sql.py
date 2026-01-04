import pandas as pd
import re
import os
import csv
import io

# ファイルパス
SQL_FILE = 'init_data.sql'
MASTER_CSV = 'station_toilet.csv'

def recover():
    print("--- 座標復元スクリプト (強化版 V2.3) を開始します ---")
    
    if not os.path.exists(SQL_FILE):
        print(f"エラー: {SQL_FILE} が見つかりません。")
        return
    if not os.path.exists(MASTER_CSV):
        print(f"エラー: {MASTER_CSV} が見つかりません。")
        return

    # 抽出用データ
    id_coords = {}
    station_backup_coords = {} 
    
    print(f"'{SQL_FILE}' を解析中...")
    
    try:
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # SQLファイル全体から INSERT INTO 文を検索（改行を跨げるように re.DOTALL を使用）
        # パターン: INSERT INTO テーブル名 (カラム...) VALUES (データ)
        # 0.0以外の座標を持つものだけを抽出
        matches = re.finditer(r"INSERT INTO (\w+) .*? VALUES\s*\((.*?)\)", content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            table_name = match.group(1).lower()
            raw_values = match.group(2).replace('\n', ' ').strip()
            
            # CSVパーサーで安全に分割
            safe_values = raw_values.replace("''", "[[Q]]")
            f_io = io.StringIO(safe_values)
            reader = csv.reader(f_io, quotechar="'", skipinitialspace=True)
            try:
                parts = next(reader)
            except:
                continue
            parts = [p.replace("[[Q]]", "'") for p in parts]
            
            if table_name == "toilets" and len(parts) >= 5:
                t_id, lat, lon = parts[0], parts[3], parts[4]
                if lat.replace('.','',1).isdigit() and lon.replace('.','',1).isdigit():
                    if float(lat) != 0:
                        id_coords[t_id] = (lat, lon)
                        
            elif table_name == "stations" and len(parts) >= 3:
                s_name, lat, lon = parts[0], parts[1], parts[2]
                if lat.replace('.','',1).isdigit() and lon.replace('.','',1).isdigit():
                    if float(lat) != 0:
                        station_backup_coords[s_name] = (lat, lon)

    except Exception as e:
        print(f"解析中にエラーが発生しました: {e}")
        return

    print(f"抽出結果: トイレ固有 {len(id_coords)}件 / 駅基準 {len(station_backup_coords)}件")

    # 2. 現在のマスタに適用
    df_master = pd.read_csv(MASTER_CSV, dtype=str).fillna('')
    recovered_count = 0
    
    for idx, row in df_master.iterrows():
        t_id = row['toilet_id']
        s_name = row['station_name']
        
        # 1. IDでマッチ
        if t_id in id_coords:
            df_master.at[idx, 'lat'], df_master.at[idx, 'lon'] = id_coords[t_id]
            recovered_count += 1
        # 2. 駅名でマッチ（予備）
        elif s_name in station_backup_coords:
            df_master.at[idx, 'lat'], df_master.at[idx, 'lon'] = station_backup_coords[s_name]
            recovered_count += 1
        else:
            df_master.at[idx, 'lat'], df_master.at[idx, 'lon'] = '0.0', '0.0'

    # 3. 保存
    df_master.to_csv(MASTER_CSV, index=False, encoding='utf-8')
    print(f"完了: {recovered_count} 件の座標を復元しました。")

if __name__ == "__main__":
    recover()