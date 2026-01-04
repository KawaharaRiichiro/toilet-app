import pandas as pd
import os

# パス設定
STRATEGIES_CSV = 'data/strategies.csv'
TOILET_MASTER_CSV = 'station_toilet.csv'

def check_integrity():
    print("--- トイレアプリ データ整合性監査レポート (詳細診断モード V2) ---\n")

    if not os.path.exists(STRATEGIES_CSV) or not os.path.exists(TOILET_MASTER_CSV):
        print("エラー: CSVファイルが不足しています。")
        return

    # すべて文字列として読み込み
    df_str = pd.read_csv(STRATEGIES_CSV, dtype=str).fillna('')
    df_tm = pd.read_csv(TOILET_MASTER_CSV, dtype=str).fillna('')

    print(f"ファイル確認:")
    print(f"  Strategies: {len(df_str)} 行")
    print(f"  Master:     {len(df_tm)} 行")
    
    # --- 構造診断 ---
    print(f"\n[構造診断] Masterファイルのカラム名と最初のデータの対応:")
    if len(df_tm) > 0:
        cols = list(df_tm.columns)
        first_vals = list(df_tm.iloc[0])
        for i in range(max(len(cols), len(first_vals))):
            c = cols[i] if i < len(cols) else "!!! カラム名不足 !!!"
            v = first_vals[i] if i < len(first_vals) else "!!! データ不足 !!!"
            print(f"  列{i+1}: [{c}] -> 値: {v}")

    print("-" * 40)

    # 1. 未調査の号車位置
    df_str['car_pos_num'] = pd.to_numeric(df_str['car_pos'], errors='coerce').fillna(0.0)
    uninvestigated = df_str[df_str['car_pos_num'] == 0.0]
    print(f"\n[1] 号車未調査(0.0)のデータ: {len(uninvestigated)} / {len(df_str)} 件")

    # 2. リンク切れチェック
    # マスタ側のIDカラムを特定
    m_id_col = 'toilet_id' if 'toilet_id' in df_tm.columns else 'id'
    
    # エラー修正: .str.strip() を使用
    master_ids = set(df_tm[m_id_col].astype(str).str.strip())
    
    # 攻略データ側のIDを整形
    df_str['target_toilet_id'] = df_str['target_toilet_id'].astype(str).str.strip()
    
    broken_links = df_str[~df_str['target_toilet_id'].isin(master_ids)]
    
    print(f"[2] IDリンク切れ: {len(broken_links)} / {len(df_str)} 件")
    if len(broken_links) > 0:
        print("    最初の3件の不一致詳細:")
        for idx, row in broken_links.head(3).iterrows():
            print(f"    - 駅: {row['station_name']}, 探しているID: '{row['target_toilet_id']}'")
            print(f"      (マスタの先頭IDサンプル: {list(master_ids)[:3]})")

    # 3. 重複チェック
    dup_subset = ['line_name', 'station_name', 'direction', 'car_pos', 'target_toilet_id']
    duplicates = df_str[df_str.duplicated(subset=[c for c in dup_subset if c in df_str.columns], keep=False)]
    print(f"[3] 攻略データの重複: {len(duplicates)} 件")

    print("\n--- 監査完了 ---")

if __name__ == "__main__":
    check_integrity()