import pandas as pd
import os

# 対象ファイル
INPUT_FILE = 'data/stations.csv'
OUTPUT_FILE = 'data/stations.csv' # 上書き保存します

def load_csv_safe(filepath):
    if not os.path.exists(filepath):
        return pd.DataFrame()
    try:
        # BOM対応かつ全列を文字列として読み込む
        df = pd.read_csv(filepath, dtype=str, encoding='utf-8-sig').fillna('')
        df.columns = df.columns.str.strip()
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(filepath, dtype=str, encoding='cp932').fillna('')
            df.columns = df.columns.str.strip()
            return df
        except:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

def main():
    print(f"読み込み中: {INPUT_FILE} ...")
    df = load_csv_safe(INPUT_FILE)
    
    if df.empty:
        print("エラー: CSVファイルが見つからないか、空です。")
        return

    # 1. 必要な列がなければ作成
    if 'dir_1_label' not in df.columns:
        df['dir_1_label'] = ''
    if 'dir_m1_label' not in df.columns:
        df['dir_m1_label'] = ''

    # 2. 数値順序の準備 (計算用)
    if 'station_order' in df.columns:
        df['order_int'] = pd.to_numeric(df['station_order'], errors='coerce').fillna(0)
    else:
        print("エラー: station_order 列がありません。")
        return

    # 3. 路線ごとにループしてラベルを生成
    # line_name のリストを取得
    lines = df['line_name'].unique()
    
    print(f"全 {len(lines)} 路線の行き先ラベルを生成します...")

    for line in lines:
        # その路線のデータだけ抽出
        mask = df['line_name'] == line
        line_data = df[mask]
        
        # 駅順でソートして始発と終点を特定
        sorted_data = line_data.sort_values('order_int')
        if sorted_data.empty: continue
        
        first_station = sorted_data.iloc[0]['station_name']
        last_station = sorted_data.iloc[-1]['station_name']
        
        # ラベルテキスト作成
        label_for_dir_1 = f"{last_station} 方面"  # 順方向(Order増)の行き先
        label_for_dir_m1 = f"{first_station} 方面" # 逆方向(Order減)の行き先
        
        # データフレームに書き込み（空欄の場合のみ埋める仕様）
        # ※もし強制的に全書き換えしたい場合は条件を外してください
        
        # dir_1_label (空欄なら埋める)
        target_mask_1 = mask & (df['dir_1_label'] == '')
        df.loc[target_mask_1, 'dir_1_label'] = label_for_dir_1
        
        # dir_m1_label (空欄なら埋める)
        target_mask_m1 = mask & (df['dir_m1_label'] == '')
        df.loc[target_mask_m1, 'dir_m1_label'] = label_for_dir_m1
        
        print(f"  - {line}: {label_for_dir_m1} / {label_for_dir_1}")

    # 4. カラムの整理 (古い不要な列を削除してスッキリさせる)
    # 残したい列の定義
    final_columns = [
        'line_name', 'line_color', 'station_order', 'station_name', 
        'lat', 'lng', 'dir_1_label', 'dir_m1_label'
    ]
    
    # 存在しない列は除外してフィルタリング
    save_cols = [c for c in final_columns if c in df.columns]
    df_out = df[save_cols]

    # 5. 上書き保存
    df_out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print("--------------------------------------------------")
    print(f"完了: {OUTPUT_FILE} を更新しました！")
    print("Excel等で開いて、中野坂上などの分岐駅だけ手動で修正してください。")

if __name__ == '__main__':
    main()
