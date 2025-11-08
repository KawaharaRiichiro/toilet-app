import pandas as pd
import io
import time
from typing import List, Dict, Any

# 新しく追加された駅トイレデータCSVのファイル名
STATION_CSV_FILE = "トイレリスト.csv"

def get_station_data_from_csv() -> List[Dict[str, Any]]:
    """
    駅のトイレデータをCSVファイルから読み込み、Supabaseスキーマに加工して返す。
    """
    print(f"\n駅トイレデータCSV ({STATION_CSV_FILE}) を読み込みます...")
    processed_list = []

    try:
        # 読み込み時にカラムが増えていることを想定し、skiprows=1で最初の行(ヘッダーと誤認されたデータ)をスキップ
        df = pd.read_csv(STATION_CSV_FILE, encoding='utf-8', header=None, skiprows=1)
        
        # ★★★ 修正点: 期待するカラム数を 6 (インデックス0〜5) に変更 ★★★
        if df.shape[1] < 6:
             print(f"エラー(駅CSV): CSVのカラム数が不足しています (期待値6カラム以上, 実測 {df.shape[1]})")
             print("ヒント: [0]名称,[1]緯度,経度,[2]車椅子,[3]駅名,[4]改札内/外,[5]住所 の順序が必要です。")
             return []
        
        # 欠損値を None に変換
        df = df.where(pd.notnull(df), None)

        for index, row in df.iterrows():
            
            # 緯度経度カラム(インデックス1)を分割
            lat_lon_str = str(row[1]).split(',')
            
            try:
                latitude = float(lat_lon_str[0].strip())
                longitude = float(lat_lon_str[1].strip())
                
                # ★★★ 新規追加: 住所の取得 ★★★
                address_str = str(row[5]).strip() if row[5] is not None else f"JR {row[3]}"
                
            except (ValueError, IndexError):
                print(f"警告: {row[0]} の緯度経度が無効です。スキップします。")
                continue

            is_wheelchair = str(row[2]).strip().lower() == 'true' if row[2] is not None else False
            inside_gate_bool = str(row[4]).strip().lower() == 'true' if row[4] is not None else False


            processed_list.append({
                'name': row[0],         
                'address': address_str, # ★★★ 修正後の住所を使用 ★★★
                'latitude': latitude,        
                'longitude': longitude,
                
                # アクセシビリティ
                'is_wheelchair_accessible': is_wheelchair,
                'has_diaper_changing_station': False, 
                'is_ostomate_accessible': False, 
                
                # 駅トイレ関連カラム
                'is_station_toilet': True,
                'station_name': row[3],
                'inside_gate': inside_gate_bool,

                # その他
                'opening_hours': None, 
                'availability_notes': None, 
                'last_synced_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'), 
            })
            
        print(f"駅トイレデータCSVから {len(processed_list)} 件のデータを取得・加工しました。")

    except FileNotFoundError:
        print(f"エラー(駅CSV): ファイルが見つかりません。{STATION_CSV_FILE}")
    except Exception as e:
        print(f"エラー(駅CSV): CSVの読み込みまたは処理中にエラーが発生しました。 {e}")
        
    return processed_list