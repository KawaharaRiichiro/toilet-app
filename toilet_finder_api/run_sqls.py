import os
import glob
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# .envファイルから接続情報を読み込む
# SUPABASE_DB_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" のような形式を想定
load_dotenv()
DB_URL = os.environ.get("SUPABASE_DB_URL")

if not DB_URL:
    print("エラー: .envファイルに SUPABASE_DB_URL が設定されていません。")
    print("形式: postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/[DB_NAME]")
    exit(1)

def get_connection():
    try:
        return psycopg2.connect(DB_URL)
    except Exception as e:
        print(f"接続エラー: {e}")
        return None

def execute_sql_file(cursor, filepath):
    print(f"実行中: {filepath} ...", end=" ", flush=True)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()
            if not sql.strip():
                print("Skip (空ファイル)")
                return
            cursor.execute(sql)
        print("OK")
    except Exception as e:
        print(f"失敗: {e}")
        raise e

def main():
    conn = get_connection()
    if not conn:
        return

    # 自動コミットモード（トランザクション管理はファイル単位で行うため）
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # 1. スキーマ定義
        if os.path.exists('01_schema.sql'):
            execute_sql_file(cur, '01_schema.sql')
        
        # 2. 駅データ (分割されている可能性も考慮)
        station_files = sorted(glob.glob('02_stations*.sql'))
        for f in station_files:
            execute_sql_file(cur, f)

        # 3. 攻略データ (分割ファイル)
        # globで取得して名前順にソート (part1, part2... の順)
        strategy_files = sorted(glob.glob('03_strategies_part*.sql'))
        if not strategy_files:
            print("警告: 03_strategies_part*.sql が見つかりません。")
        
        for f in strategy_files:
            execute_sql_file(cur, f)

        print("\n全SQLファイルの実行が完了しました！")

    except Exception as e:
        print("\n処理を中断しました。")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()