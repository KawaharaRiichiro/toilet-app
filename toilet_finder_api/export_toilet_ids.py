import pandas as pd
import uuid
import os
from station_data_importer import get_station_data_from_csv

# このスクリプトは、station_toilet.csv から固定IDを生成して一覧表示します
# ホームドアデータ(station_doors.csv) を作成する際のリファレンスとして使ってください

def main():
    print("トイレIDリストを生成中...")
    
    # 駅トイレデータを取得
    station_data = get_station_data_from_csv()
    
    if not station_data:
        print("データがありませんでした。")
        return

    # 必要な項目だけ抽出してDataFrameにする
    df_out = pd.DataFrame(station_data)[['station_name', 'name', 'address', 'id']]
    
    # カラム名をわかりやすく
    df_out.columns = ['駅名', 'トイレ表示名', '住所(場所)', '固定ID (これをコピー)']
    
    # CSVに出力
    output_file = "toilet_id_list.csv"
    df_out.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n完了！ '{output_file}' を作成しました。")
    print("このファイルを開いて、ホームドアデータ (station_doors.csv) の nearest_toilet_id 列にIDを貼り付けてください。")

if __name__ == "__main__":
    main()