import pandas as pd
import time
from typing import List, Dict, Any

# 駅トイレデータCSVのファイル名
STATION_CSV_FILE = "トイレリスト.csv"

def get_station_data_from_csv() -> List[Dict[str, Any]]:
    """
    駅のトイレデータをCSVファイルから読み込み、Supabaseスキーマに加工して返す。
    """
    print(f"駅トイレデータCSV ({STATION_CSV_FILE}) を読み込みます...")
    processed_list = []

    try:
        # header=None, skiprows=1 で、1行目をスキップしてデータのみ読み込む
        # ※実際のCSVに合わせて調整が必要な場合があります
        df = pd.read_csv(STATION_CSV_FILE, encoding='utf-8', header=None, skiprows=1)
        
        # カラム数チェック (最低限必要な6カラムがあるか)
        if df.shape[1] < 6:
             print(f"エラー(駅CSV): CSVのカラム数が不足しています (実測 {df.shape[1]})")
             return []
        
        # 欠損値(NaN)をNoneに変換
        df = df.where(pd.notnull(df), None)

        for _, row in df.iterrows():
            # 必須データのチェック
            if row[0] is None or row[1] is None: # 名称と座標は必須
                 continue

            try:
                # 座標の分割と変換 ("緯度,経度" の形式を想定)
                lat_lon = str(row[1]).split(',')
                if len(lat_lon) != 2:
                    raise ValueError("座標フォーマットエラー")
                latitude = float(lat_lon[0].strip())
                longitude = float(lat_lon[1].strip())

                # 住所の生成
                address_str = str(row[5]) if row[5] else f"{row[3]} 構内"
                
            except (ValueError, IndexError):
                print(f"警告: {row[0]} のデータ形式が無効です。スキップします。")
                continue

            # ブール値への変換 ('TRUE'/'FALSE'文字列などを想定)
            is_wheelchair = str(row[2]).strip().upper() == 'TRUE' if row[2] else False
            inside_gate_bool = str(row[4]).strip().upper() == 'TRUE' if row[4] else False

            # 現在時刻の文字列
            current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

            processed_list.append({
                'name': row[0],         
                'address': address_str, 
                'latitude': latitude,        
                'longitude': longitude,
                
                # アクセシビリティ (CSVにない項目はFalse固定)
                'is_wheelchair_accessible': is_wheelchair,
                'has_diaper_changing_station': False, 
                'is_ostomate_accessible': False, 
                
                # 駅トイレ関連
                'is_station_toilet': True,
                'inside_gate': inside_gate_bool,

                # その他
                'opening_hours': None, 
                'availability_notes': None, 

                # ★★★ 必須カラムを追加 ★★★
                'created_at': current_time,
                'updated_at': current_time,
            })
            
        print(f"駅トイレデータCSVから {len(processed_list)} 件のデータを取得・加工しました。")
        return processed_list

    except FileNotFoundError:
        print(f"エラー: 駅トイレデータCSV ({STATION_CSV_FILE}) が見つかりません。")
        return []
    except Exception as e:
        print(f"駅トイレデータの読み込み中に予期せぬエラーが発生しました: {e}")
        return []