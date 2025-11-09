import pandas as pd
import time
import uuid
from typing import List, Dict, Any

# ファイル名を定義
STATION_CSV_FILE = "station_toilet.csv"

def get_station_data_from_csv() -> List[Dict[str, Any]]:
    print(f"駅トイレデータCSV ({STATION_CSV_FILE}) を読み込みます...")
    processed_list = []

    try:
        try:
            df = pd.read_csv(STATION_CSV_FILE, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(STATION_CSV_FILE, encoding='cp932')

        for _, row in df.iterrows():
            # ★修正: 英語('name') と 日本語('名称') の両方に対応
            name = row.get('name') or row.get('名称')
            if pd.isna(name): continue

            # IDの取得
            toilet_id = str(row.get('id')).strip() if pd.notna(row.get('id')) else str(uuid.uuid4())

            try:
                # 座標の取得 ("latitude,longitude" という結合カラムにも対応)
                lat_lon_val = row.get('latitude,longitude') or row.get('座標')
                if pd.notna(lat_lon_val) and ',' in str(lat_lon_val):
                    lat_str, lon_str = str(lat_lon_val).split(',')
                    lat = float(lat_str.strip('" '))
                    lon = float(lon_str.strip('" '))
                else:
                    lat = float(row.get('latitude') or row.get('緯度'))
                    lon = float(row.get('longitude') or row.get('経度'))
            except (ValueError, TypeError):
                 print(f"警告: {name} の座標が無効です。スキップします。")
                 continue

            def to_bool(val):
                return str(val).strip().upper() in ['TRUE', 'YES', '1', 'あり', '○']

            current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

            processed_list.append({
                'id': toilet_id,
                'name': name,
                'address': row.get('address') or row.get('住所') or f"{row.get('station_name') or row.get('駅名')} 構内",
                'latitude': lat,
                'longitude': lon,
                'is_wheelchair_accessible': to_bool(row.get('is_wheelchair_accessible') or row.get('車椅子')),
                'has_diaper_changing_station': False,
                'is_ostomate_accessible': False,
                'is_station_toilet': True,
                'inside_gate': to_bool(row.get('inside_gate') or row.get('改札内')),
                'opening_hours': None,
                'availability_notes': None,
                'created_at': current_time,
                'updated_at': current_time,
            })
            
        print(f"駅トイレデータCSVから {len(processed_list)} 件のデータを取得・加工しました。")
        return processed_list

    except FileNotFoundError:
        print(f"エラー: {STATION_CSV_FILE} が見つかりません。")
        return []
    except Exception as e:
        print(f"駅トイレデータの読み込みエラー: {e}")
        return []