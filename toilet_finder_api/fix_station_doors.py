import pandas as pd
import shutil
import os

def main():
    print("station_doors.csv の修復を開始します...")

    # ファイルの読み込み
    try:
        df_doors = pd.read_csv('station_doors.csv')
        df_toilets = pd.read_csv('toilet_id_list.csv')
    except FileNotFoundError as e:
        print(f"エラー: ファイルが見つかりません。{e}")
        return

    # トイレリストから必要な情報を抽出
    # toilet_id_list.csvのカラム: ['駅名', 'トイレ表示名', '住所(場所)', '固定ID (これをコピー)']
    # 0番目が駅名、3番目がIDと仮定します
    station_col_name = df_toilets.columns[0] # 駅名
    id_col_name = df_toilets.columns[3]      # 固定ID

    # 「駅名 -> トイレID」の辞書を作成 (同じ駅に複数ある場合は最初の1つを採用)
    station_to_id_map = {}
    for _, row in df_toilets.iterrows():
        s_name = str(row[station_col_name])
        t_id = row[id_col_name]
        if s_name not in station_to_id_map:
            station_to_id_map[s_name] = t_id

    # 有効なIDのセット（高速検索用）
    valid_ids = set(df_toilets[id_col_name])
    
    # とにかく何でもいいから有効なID（フォールバック用）
    fallback_id = df_toilets.iloc[0][id_col_name]

    # 修正ロジック
    def get_valid_id(row):
        current_id = row.get('nearest_toilet_id')
        station = str(row.get('station_name'))

        # すでに有効なIDならそのまま
        if current_id in valid_ids:
            return current_id
        
        # その駅のトイレIDがあればそれを使う
        if station in station_to_id_map:
            return station_to_id_map[station]
        
        # なければ適当なIDを使う（エラー回避）
        return fallback_id

    # バックアップ作成
    if not os.path.exists('station_doors_backup.csv'):
        shutil.copy('station_doors.csv', 'station_doors_backup.csv')
        print("バックアップを作成しました: station_doors_backup.csv")

    # 適用
    df_doors['nearest_toilet_id'] = df_doors.apply(get_valid_id, axis=1)

    # 保存
    df_doors.to_csv('station_doors.csv', index=False, encoding='utf-8')
    print(f"完了！ station_doors.csv を更新しました。")
    print("次に 'python import.py' を実行してください。")

if __name__ == "__main__":
    main()