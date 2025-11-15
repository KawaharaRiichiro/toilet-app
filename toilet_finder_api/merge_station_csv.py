import pandas as pd
import os

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
# 元々のシステムが期待している列名（ターゲット）
TARGET_COLUMNS = [
    "station_name",
    "line_name",
    "lat",
    "lon",
    "wheelchair",
    "baby_chair",
    "ostomate",
    "opening_hours",
    "notes"
]

OSM_FILE = "station_toilet_osm.csv"
TARGET_FILE = "station_toilet.csv"

def main():
    print("=== CSVデータの統合を開始します ===")

    # 1. OSMデータの読み込み
    if not os.path.exists(OSM_FILE):
        print(f"エラー: {OSM_FILE} が見つかりません。先に generate_station_csv.py を実行してください。")
        return

    df_osm = pd.read_csv(OSM_FILE)
    print(f"OSMデータ読み込み: {len(df_osm)} 件")

    # 2. 既存データの読み込み（存在する場合）
    if os.path.exists(TARGET_FILE):
        try:
            df_existing = pd.read_csv(TARGET_FILE)
            print(f"既存データ読み込み: {len(df_existing)} 件")
        except:
            df_existing = pd.DataFrame(columns=TARGET_COLUMNS)
            print("既存データ読み込み: 0 件 (新規作成)")
    else:
        df_existing = pd.DataFrame(columns=TARGET_COLUMNS)
        print("既存データなし (新規作成)")

    # 3. OSMデータをターゲット形式に変換
    df_converted = pd.DataFrame()

    # カラムのマッピングと変換
    df_converted["station_name"] = df_osm["station_name"]
    
    # line_name (OSMデータには含まれていない場合があるため、なければ'不明'などにする)
    if "line" in df_osm.columns:
        df_converted["line_name"] = df_osm["line"]
    else:
        df_converted["line_name"] = "各線" 

    df_converted["lat"] = df_osm["lat"]
    df_converted["lon"] = df_osm["lon"]
    
    # 属性データ
    df_converted["wheelchair"] = df_osm["wheelchair"].fillna("")
    
    # カラム名の違いを吸収 (baby -> baby_chair)
    if "baby" in df_osm.columns:
        df_converted["baby_chair"] = df_osm["baby"].fillna("")
    else:
        df_converted["baby_chair"] = ""

    df_converted["ostomate"] = df_osm["ostomate"].fillna("")
    
    # デフォルト値の設定
    df_converted["opening_hours"] = "始発〜終電"
    
    # toilet_name (場所の詳細) を notes に結合する
    # 例: notes = "東口トイレ (OpenStreetMapデータ)"
    def make_note(row):
        t_name = str(row.get("toilet_name", ""))
        orig_note = str(row.get("note", ""))
        if t_name == "nan": t_name = ""
        if orig_note == "nan": orig_note = ""
        
        return f"{t_name} {orig_note}".strip()

    df_converted["notes"] = df_osm.apply(make_note, axis=1)

    # 4. データの結合
    # 既存データ + 新しいOSMデータ
    df_merged = pd.concat([df_existing, df_converted], ignore_index=True)

    # 5. 重複の削除（完全に緯度経度が一致するものは削除）
    before_len = len(df_merged)
    df_merged = df_merged.drop_duplicates(subset=['lat', 'lon'], keep='last')
    after_len = len(df_merged)
    
    if before_len > after_len:
        print(f"重複削除: {before_len - after_len} 件の重複を除外しました。")

    # 6. 保存
    # 必要なカラムだけに絞って保存
    df_final = df_merged[TARGET_COLUMNS]
    df_final.to_csv(TARGET_FILE, index=False, encoding='utf-8')

    print(f"\n完了！ 合計 {len(df_final)} 件のデータを '{TARGET_FILE}' に保存しました。")
    print("次に 'python import.py' を実行すると、これらのデータが取り込まれます。")

if __name__ == "__main__":
    main()