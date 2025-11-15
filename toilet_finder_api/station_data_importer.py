import pandas as pd
import uuid
import time
import os

# CSVファイル名
STATION_CSV_FILE = "station_toilet.csv"

def get_station_data_from_csv():
    """
    station_toilet.csv を読み込み、Supabase登録用の形式に変換して返す
    """
    if not os.path.exists(STATION_CSV_FILE):
        print(f"  [Warning] {STATION_CSV_FILE} が見つかりません。駅データはスキップします。")
        return []

    print(f"駅トイレデータCSV ({STATION_CSV_FILE}) を読み込みます...")
    
    try:
        df = pd.read_csv(STATION_CSV_FILE, encoding='utf-8')
        
        if 'lat' not in df.columns or 'lon' not in df.columns:
            print("  [Error] CSVに 'lat' または 'lon' 列がありません。")
            return []

        processed_data = []
        
        for _, row in df.iterrows():
            if pd.isna(row.get('lat')) or pd.isna(row.get('lon')):
                continue

            def is_avail(val):
                if pd.isna(val): return False
                return str(val).strip() in ['○', '有', 'あり', 'TRUE', 'True', 'true', 'yes']

            wheelchair = is_avail(row.get('wheelchair'))
            baby = is_avail(row.get('baby_chair'))
            ostomate = is_avail(row.get('ostomate'))

            st_name = str(row.get('station_name', '不明な駅'))
            line = str(row.get('line_name', ''))
            notes = str(row.get('notes', ''))
            
            display_name = st_name
            address = f"{line} {st_name}" if line else st_name

            # 【重要】IDを固定化するロジック (UUID v5)
            # "駅名_表示名" という文字列が同じなら、常に同じIDが生成されます
            unique_string = f"{st_name}_{display_name}_{address}"
            fixed_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))

            data = {
                "id": fixed_id, # 固定IDを使用
                "name": display_name,
                "address": address,
                "latitude": float(row['lat']),
                "longitude": float(row['lon']),
                "opening_hours": row.get('opening_hours', '始発〜終電'),
                "availability_notes": notes,
                "is_wheelchair_accessible": wheelchair,
                "has_diaper_changing_station": baby,
                "is_ostomate_accessible": ostomate,
                "is_station_toilet": True,
                "station_name": st_name,
                "inside_gate": "改札内" in notes,
                "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "average_rating": 0.0,
                "review_count": 0,
                "last_synced_at": time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            processed_data.append(data)

        print(f"駅トイレデータCSVから {len(processed_data)} 件のデータを取得・加工しました。")
        return processed_data

    except Exception as e:
        print(f"  [Error] 駅データ読み込み中にエラーが発生しました: {e}")
        return []

if __name__ == "__main__":
    data = get_station_data_from_csv()
    print(f"取得件数: {len(data)}")