import os
import requests
import pandas as pd
import io
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from station_data_importer import get_station_data_from_csv # ★★★ 新規インポート ★★★


# -----------------------------------------------------------------
# 1. 設定
# -----------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME = 'toilets'
SUMIDA_API_URL = "https://service.api.metro.tokyo.lg.jp/api/t131075d0000000137-955e33d5f6e6df2b07b523cd05679ad3-0/json"
SHINJUKU_CSV_URL = "https://www.city.shinjuku.lg.jp/content/000399974.csv"


# -----------------------------------------------------------------
# 2. データ取得関数 (墨田区) - API版 (変更なし)
# -----------------------------------------------------------------
def get_sumida_data():
    """ 墨田区のトイレデータをAPIから取得し、Supabaseのスキーマ形式に加工する """
    # ... (墨田区のデータ取得・加工ロジックは省略) ...
    # ※ 変更はありませんが、ここではスペース節約のため省略します。実際は元のコードが必要です。
    print(f"墨田区のトイレデータ取得開始 (API: {SUMIDA_API_URL})...")
    processed_list = []
    
    try:
        response = requests.post(SUMIDA_API_URL, json={})
        response.raise_for_status() 
        data = response.json()
        
        toilet_list = None
        for key, value in data.items():
            if isinstance(value, list):
                toilet_list = value
                break
        
        if not toilet_list:
            print("エラー(墨田区): APIが返した辞書内にリスト形式のデータが見つかりませんでした。")
            return []

        print(f"API(墨田区)から {len(toilet_list)} 件のトイレ情報を加工します。")

        for item in toilet_list:
            start_time = item.get('利用開始時間')
            end_time = item.get('利用終了時間')
            opening_hours = None
            if start_time and end_time:
                opening_hours = f"{start_time} - {end_time}"
            
            is_wheelchair = bool(item.get('バリアフリートイレ数'))

            processed_list.append({
                'name': item.get('名称'),         
                'address': item.get('所在地_連結表記'), 
                'latitude': item.get('緯度'),        
                'longitude': item.get('経度'),
                'opening_hours': opening_hours, 
                'availability_notes': item.get('備考'), 
                'is_wheelchair_accessible': is_wheelchair,
                'has_diaper_changing_station': bool(item.get('乳幼児用設備設置トイレ有無')),
                'is_ostomate_accessible': bool(item.get('オストメイト設置トイレ有無')),
                
                'is_station_toilet': False,
                'station_name': None,
                'inside_gate': None,
                
                'last_synced_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'), 
            })
            
        print("API(墨田区)のデータ加工が完了しました。")
            
    except requests.exceptions.RequestException as e:
        print(f"エラー(墨田区): APIからのデータ取得に失敗しました。 {e}")
    except Exception as e:
        print(f"エラー(墨田区): データの処理中にエラーが発生しました。 {e}")
        
    return processed_list


# -----------------------------------------------------------------
# 3. データ取得関数 (新宿区) - CSV直リンク版 (変更なし)
# -----------------------------------------------------------------
def get_shinjuku_data():
    """ 新宿区のトイレデータをCSV直リンクから直接取得し、Supabaseのスキーマ形式に加工する """
    # ... (新宿区のデータ取得・加工ロジックは省略) ...
    # ※ 変更はありませんが、ここではスペース節約のため省略します。実際は元のコードが必要です。
    print(f"新宿区のデータセットCSVにアクセス: {SHINJUKU_CSV_URL} ...")
    processed_list = []

    try:
        response = requests.get(SHINJUKU_CSV_URL)
        response.raise_for_status() 

        csv_content = response.content.decode('utf-16')
        df = pd.read_csv(io.StringIO(csv_content))
        print(f"CSV(新宿区)から {len(df)} 件のトイレ情報を取得しました。")
        df = df.where(pd.notnull(df), None)

        for index, row in df.iterrows():
            start_time = row.get('利用開始時間')
            end_time = row.get('利用終了時間')
            opening_hours = None
            if start_time and end_time:
                opening_hours = f"{start_time} - {end_time}"

            processed_list.append({
                'name': row.get('名称'),       
                'address': row.get('所在地_連結表記'), 
                'latitude': row.get('緯度'),       
                'longitude': row.get('経度'),      
                'opening_hours': opening_hours,
                'availability_notes': row.get('利用可能時間特記事項'), 
                'is_wheelchair_accessible': True if row.get('車椅子使用者用トイレ有無') == '有' else False,
                'has_diaper_changing_station': True if row.get('乳幼児用設備設置トイレ有無') == '有' else False,
                'is_ostomate_accessible': True if row.get('オストメイト設置トイレ有無') == '有' else False,
                
                'is_station_toilet': False,
                'station_name': None,
                'inside_gate': None,
                
                'last_synced_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'), 
            })
        
        print("CSV(新宿区)のデータ加工が完了しました。")

    except requests.exceptions.RequestException as e:
        print(f"エラー(新宿区): CSVのダウンロードに失敗しました。 {e}")
    except UnicodeDecodeError as e:
        print(f"エラー(新宿区): CSVのエンコード(文字コード)に失敗しました。 {e}")
    except Exception as e:
        print(f"エラー(新宿区): CSVの読み込みまたは処理中にエラーが発生しました。 {e}")

    return processed_list


# -----------------------------------------------------------------
# 4. Supabase更新関数 (変更なし)
# -----------------------------------------------------------------
def update_supabase_data(data_list):
    if not data_list:
        print("\n登録するデータが0件のため、Supabaseの更新をスキップします。")
        return

    print(f"\n合計 {len(data_list)} 件のトイレデータをSupabaseに登録します...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print(f"Supabaseの既存トイレデータ({TABLE_NAME})を全件削除します...")
        delete_response = supabase.table(TABLE_NAME).delete().gt('created_at', '1970-01-01').execute()
        print("既存データの削除が完了しました。")

        print(f"Supabaseに {len(data_list)} 件のデータを Insert (挿入) します...")
        CHUNK_SIZE = 500 
        for i in range(0, len(data_list), CHUNK_SIZE):
            chunk = data_list[i:i + CHUNK_SIZE]
            insert_response = supabase.table(TABLE_NAME).insert(chunk).execute()
            print(f"  ... {i + len(chunk)} / {len(data_list)} 件 挿入完了")

        print("\nデータの同期が正常に完了しました！")
    except Exception as e:
        print(f"\nエラー(Supabase): データベースの更新に失敗しました。")
        if hasattr(e, 'details'): print(f"  詳細: {e.details}")
        elif hasattr(e, 'message'): print(f"  詳細: {e.message}")
        else: print(f"  詳細: {e}")

# -----------------------------------------------------------------
# 5. メイン実行処理 (main関数)
# -----------------------------------------------------------------
def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("エラー: 環境変数 SUPABASE_URL または SUPABASE_KEY が設定されていません。")
        print(".env ファイルを作成し、設定してください。")
        return
    print("--- トイレデータ同期バッチ開始 ---")
    all_toilets = []
    
    # 公衆トイレデータ
    all_toilets.extend(get_sumida_data())
    all_toilets.extend(get_shinjuku_data())
    
    # ★★★ 駅トイレデータ (インポートした関数を呼び出す) ★★★
    all_toilets.extend(get_station_data_from_csv()) 
    
    update_supabase_data(all_toilets)
    print("--- トイレデータ同期バッチ終了 ---")

if __name__ == "__main__":
    main()