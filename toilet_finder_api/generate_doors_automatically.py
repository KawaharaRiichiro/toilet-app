import pandas as pd
import os

# ---------------------------------------------------------
# 1. 設定：各路線の「車両数」と「方向」の定義
# ---------------------------------------------------------
# ここに定義がない路線は、デフォルト設定（10両、上り/下り）で作られます。
# 必要に応じて書き換えてください。

LINE_CONFIG = {
    # --- JR線 ---
    "JR山手線": {
        "cars": 11, 
        "dirs": ["内回り", "外回り"] 
    },
    "JR中央線": {
        "cars": 10, 
        "dirs": ["東京方面", "高尾方面"] 
    },
    "JR京浜東北線": {
        "cars": 10, 
        "dirs": ["大宮方面", "大船方面"] 
    },
    "JR総武線": {
        "cars": 10, 
        "dirs": ["三鷹方面", "千葉方面"] 
    },
    "JR埼京線": {
        "cars": 10, 
        "dirs": ["大宮方面", "大崎/新宿方面"] 
    },
    "JR湘南新宿ライン": {
        "cars": 15, 
        "dirs": ["大宮方面", "大船方面"] 
    },

    # --- 地下鉄 ---
    "東京メトロ銀座線": {
        "cars": 6, 
        "dirs": ["浅草方面", "渋谷方面"] 
    },
    "東京メトロ丸ノ内線": {
        "cars": 6, 
        "dirs": ["池袋方面", "荻窪方面"] 
    },
    "東京メトロ日比谷線": {
        "cars": 7, 
        "dirs": ["北千住方面", "中目黒方面"] 
    },
    "東京メトロ東西線": {
        "cars": 10, 
        "dirs": ["西船橋方面", "中野方面"] 
    },
    "東京メトロ千代田線": {
        "cars": 10, 
        "dirs": ["綾瀬方面", "代々木上原方面"] 
    },
    "東京メトロ有楽町線": {
        "cars": 10, 
        "dirs": ["新木場方面", "和光市方面"] 
    },
    "東京メトロ半蔵門線": {
        "cars": 10, 
        "dirs": ["押上方面", "渋谷方面"] 
    },
    "東京メトロ南北線": {
        "cars": 6, 
        "dirs": ["赤羽岩淵方面", "目黒方面"] 
    },
    "東京メトロ副都心線": {
        "cars": 10, 
        "dirs": ["和光市方面", "渋谷方面"] 
    },
    "都営大江戸線": {
        "cars": 8, 
        "dirs": ["内回り", "外回り"] # または光が丘方面/都庁前方面
    },
    "都営浅草線": {
        "cars": 8, 
        "dirs": ["押上方面", "西馬込方面"] 
    },
    "都営三田線": {
        "cars": 8, 
        "dirs": ["西高島平方面", "目黒方面"] 
    },
    "都営新宿線": {
        "cars": 10, 
        "dirs": ["本八幡方面", "新宿方面"] 
    },

    # --- 私鉄 ---
    "東急東横線": {
        "cars": 10, 
        "dirs": ["渋谷方面", "横浜方面"] 
    },
    "東急田園都市線": {
        "cars": 10, 
        "dirs": ["渋谷方面", "中央林間方面"] 
    },
    "小田急小田原線": {
        "cars": 10, 
        "dirs": ["新宿方面", "小田原方面"] 
    },
    "京王線": {
        "cars": 10, 
        "dirs": ["新宿方面", "京王八王子方面"] 
    },
    "西武池袋線": {
        "cars": 10, 
        "dirs": ["池袋方面", "飯能方面"] 
    },
    "西武新宿線": {
        "cars": 10, 
        "dirs": ["西武新宿方面", "本川越方面"] 
    },
}

# デフォルト設定（リストにない路線用）
DEFAULT_CONFIG = {
    "cars": 10,
    "dirs": ["上り", "下り"]
}

# ファイル名
INPUT_FILE = "station_toilet.csv"
OUTPUT_FILE = "station_doors.csv"

def main():
    print("=== ホームドアデータ自動生成（方向付き）を開始します ===")

    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。")
        return

    # 1. 駅トイレデータを読み込む
    df_stations = pd.read_csv(INPUT_FILE)
    print(f"読み込み駅数: {len(df_stations)} 駅")

    door_data_list = []

    # 2. 駅ごとにループ
    for index, row in df_stations.iterrows():
        station_name = row['station_name']
        line_name = row['line_name']
        toilet_id = row['id']

        # その路線の設定を取得（なければデフォルト）
        config = LINE_CONFIG.get(line_name, DEFAULT_CONFIG)
        car_count = config["cars"]
        directions = config["dirs"]

        # 3. 方向ごとにループ (例: 内回り → 外回り)
        for direction in directions:
            
            # 4. 1号車からN号車までループ
            for car_num in range(1, car_count + 1):
                
                # ドア番号（簡易的に1番ドアのみ作成）
                door_num = 1 

                door_row = {
                    "station_name": station_name,
                    "line_name": line_name,
                    "direction": direction,      # ★ここが変わります
                    "car_number": car_num,
                    "door_number": door_num,
                    "nearest_toilet_id": toilet_id # 現状は駅の代表トイレIDが入ります
                }
                door_data_list.append(door_row)

    # 4. CSV保存
    df_doors = pd.DataFrame(door_data_list)
    df_doors.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print(f"\n完了！ 合計 {len(df_doors)} 件のドアデータを生成しました。")
    print(f"ファイル: {OUTPUT_FILE}")
    print("\n【重要】")
    print("作成されたCSVでは、上りも下りも『同じトイレID』になっています。")
    print("より正確にするには、Excel等でCSVを開き、方向ごとに正しいトイレIDに書き換えてください。")
    print("修正後、'python import.py' を実行してDBに登録してください。")

if __name__ == "__main__":
    main()