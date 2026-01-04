import pandas as pd
import os

# 対象ファイル
TARGET_CSV = 'data/strategies.csv'

# ---------------------------------------------------------
# 路線ごとのホーム規則定義
# ---------------------------------------------------------
# key: 路線名
# value: { 方向(1/-1): "ホーム名" }
# ※一般的な相対式ホーム・島式ホームの規則を定義しています。
# ※ターミナル駅などのイレギュラーは後で手動修正が必要です。

PLATFORM_RULES = {
    # --- 東京メトロ ---
    "銀座線": {1: "1番線", -1: "2番線"}, # 1:渋谷, -1:浅草
    "丸ノ内線": {1: "1番線", -1: "2番線"}, # 1:荻窪, -1:池袋
    "日比谷線": {1: "1番線", -1: "2番線"}, # 1:中目黒, -1:北千住
    "東西線": {1: "1番線", -1: "2番線"},   # 1:西船橋, -1:中野
    "千代田線": {1: "1番線", -1: "2番線"}, # 1:代々木上原, -1:綾瀬
    "有楽町線": {1: "1番線", -1: "2番線"}, # 1:新木場, -1:和光市
    "半蔵門線": {1: "1番線", -1: "2番線"}, # 1:渋谷/中央林間, -1:押上
    "南北線": {1: "1番線", -1: "2番線"},   # 1:赤羽岩淵, -1:目黒
    "副都心線": {1: "1番線", -1: "2番線"}, # 1:渋谷, -1:和光市

    # --- 都営地下鉄 ---
    "都営浅草線": {1: "1番線", -1: "2番線"}, # 1:西馬込, -1:押上
    "都営三田線": {1: "1番線", -1: "2番線"}, # 1:目黒, -1:西高島平
    "都営新宿線": {1: "1番線", -1: "2番線"}, # 1:新宿, -1:本八幡
    "都営大江戸線": {1: "1番線", -1: "2番線"}, # 1:六本木/大門, -1:都庁前/光が丘

    # --- JR線 (代表的なホーム) ---
    # 山手線などの環状線や複々線は駅によりバラバラですが、
    # 一旦「内回り/外回り」「下り/上り」の慣例で埋めます。
    "JR山手線": {1: "内回りホーム", -1: "外回りホーム"}, 
    "JR京浜東北線": {1: "1番線", -1: "2番線"}, # 南行/北行
    "JR中央線": {1: "1番線", -1: "2番線"},     # 下り/上り
    "JR総武線": {1: "1番線", -1: "2番線"},     # 下り/上り
    
    # --- 私鉄 ---
    "小田急小田原線": {1: "1番線", -1: "2番線"}, # 1:小田原, -1:新宿
    "東急東横線": {1: "1番線", -1: "2番線"},     # 1:横浜, -1:渋谷
}

def load_csv_safe(filepath):
    if not os.path.exists(filepath):
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath, dtype=str, encoding='utf-8-sig').fillna('')
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

def main():
    print(f"読み込み中: {TARGET_CSV} ...")
    df = load_csv_safe(TARGET_CSV)
    
    if df.empty:
        print("エラー: CSVファイルが見つからないか、空です。")
        return

    # platform_name列がなければ作成
    if 'platform_name' not in df.columns:
        df['platform_name'] = ''

    update_count = 0

    # 行ごとに処理
    for index, row in df.iterrows():
        line_name = row['line_name']
        direction = row.get('direction')
        current_platform = row.get('platform_name', '')
        
        # 既に値が入っている場合はスキップ (銀座線など)
        if current_platform and current_platform != 'nan':
            continue

        # 路線名の一部一致でルールを探す (JR中央線快速 -> JR中央線)
        rule = None
        for key in PLATFORM_RULES:
            if key in line_name:
                rule = PLATFORM_RULES[key]
                break
        
        if rule:
            try:
                # directionは文字列の可能性があるのでint変換
                d = int(float(direction)) if direction else 1
                
                # ルール適用
                new_platform = rule.get(d, "ホーム")
                
                # DataFrame更新
                df.at[index, 'platform_name'] = new_platform
                update_count += 1
            except:
                pass # directionが不正な場合はスキップ

    # 保存
    df.to_csv(TARGET_CSV, index=False, encoding='utf-8-sig')
    
    print("--------------------------------------------------")
    print(f"完了: {update_count} 件のホーム情報を補完しました！")
    print(f"保存先: {TARGET_CSV}")
    print("※これは一般的な規則に基づく自動入力です。")
    print("  渋谷、新宿、東京などのターミナル駅は手動修正を推奨します。")

if __name__ == '__main__':
    main()