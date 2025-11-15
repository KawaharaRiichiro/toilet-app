import pandas as pd
import os

# ---------------------------------------------------------
# 1. 設定：各路線の「車両数」と「方向」の定義
# ---------------------------------------------------------
LINE_CONFIG = {
    # --- JR線 ---
    "JR山手線": { "cars": 11, "dirs": ["内回り", "外回り"] },
    "JR中央線": { "cars": 10, "dirs": ["東京方面", "高尾方面"] },
    "JR京浜東北線": { "cars": 10, "dirs": ["大宮方面", "大船方面"] },
    "JR総武線": { "cars": 10, "dirs": ["三鷹方面", "千葉方面"] },
    "JR埼京線": { "cars": 10, "dirs": ["大宮方面", "大崎/新宿方面"] },
    "JR湘南新宿ライン": { "cars": 15, "dirs": ["大宮方面", "大船方面"] },
    # --- 地下鉄 ---
    "東京メトロ銀座線": { "cars": 6, "dirs": ["浅草方面", "渋谷方面"] },
    "東京メトロ丸ノ内線": { "cars": 6, "dirs": ["池袋方面", "荻窪方面"] },
    "東京メトロ日比谷線": { "cars": 7, "dirs": ["北千住方面", "中目黒方面"] },
    "東京メトロ東西線": { "cars": 10, "dirs": ["西船橋方面", "中野方面"] },
    "東京メトロ千代田線": { "cars": 10, "dirs": ["綾瀬方面", "代々木上原方面"] },
    "東京メトロ有楽町線": { "cars": 10, "dirs": ["新木場方面", "和光市方面"] },
    "東京メトロ半蔵門線": { "cars": 10, "dirs": ["押上方面", "渋谷方面"] },
    "東京メトロ南北線": { "cars": 6, "dirs": ["赤羽岩淵方面", "目黒方面"] },
    "東京メトロ副都心線": { "cars": 10, "dirs": ["和光市方面", "渋谷方面"] },
    "都営大江戸線": { "cars": 8, "dirs": ["内回り", "外回り"] },
    "都営浅草線": { "cars": 8, "dirs": ["押上方面", "西馬込方面"] },
    "都営三田線": { "cars": 8, "dirs": ["西高島平方面", "目黒方面"] },
    "都営新宿線": { "cars": 10, "dirs": ["本八幡方面", "新宿方面"] },
    # --- 私鉄 ---
    "東急東横線": { "cars": 10, "dirs": ["渋谷方面", "横浜方面"] },
    "東急田園都市線": { "cars": 10, "dirs": ["渋谷方面", "中央林間方面"] },
    "小田急小田原線": { "cars": 10, "dirs": ["新宿方面", "小田原方面"] },
    "京王線": { "cars": 10, "dirs": ["新宿方面", "京王八王子方面"] },
    "西武池袋線": { "cars": 10, "dirs": ["池袋方面", "飯能方面"] },
    "西武新宿線": { "cars": 10, "dirs": ["西武新宿方面", "本川越方面"] },
}
DEFAULT_CONFIG = { "cars": 10, "dirs": ["上り", "下り"] }

INPUT_FILE = "station_toilet.csv"
OUTPUT_FILE = "station_doors.csv"

def main():
    print("=== ドアデータ再生成（ID整合性修正版）を開始します ===")

    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。")
        return

    df_stations = pd.read_csv(INPUT_FILE)
    
    # 【重要】駅ごとに「代表トイレID」を1つ決める
    # (同じ駅に複数のトイレがある場合、リストの最初にあるものを代表とする)
    station_toilet_map = {} # {(line_name, station_name): toilet_id}

    for _, row in df_stations.iterrows():
        s_name = str(row.get('station_name', ''))
        l_name = str(row.get('line_name', ''))
        t_id = str(row.get('id', ''))
        
        if not s_name or not t_id: continue
        
        key = (l_name, s_name)
        # まだ登録されていなければ登録（これがその駅の代表IDになる）
        if key not in station_toilet_map:
            station_toilet_map[key] = t_id

    print(f"紐付け対象の駅数: {len(station_toilet_map)}")

    # ドアデータの生成
    door_data_list = []

    for (line_name, station_name), toilet_id in station_toilet_map.items():
        config = LINE_CONFIG.get(line_name, DEFAULT_CONFIG)
        
        for direction in config["dirs"]:
            for car_num in range(1, config["cars"] + 1):
                door_row = {
                    "station_name": station_name,
                    "line_name": line_name,
                    "direction": direction,
                    "car_number": car_num,
                    "door_number": 1,
                    "nearest_toilet_id": toilet_id # 代表IDをセット
                }
                door_data_list.append(door_row)

    # 保存
    df_doors = pd.DataFrame(door_data_list)
    df_doors.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print(f"\n完了！ 合計 {len(df_doors)} 件のドアデータを再生成しました。")
    print(f"保存先: {OUTPUT_FILE}")
    print("最後に 'python import.py' を実行してください。")

if __name__ == "__main__":
    main()