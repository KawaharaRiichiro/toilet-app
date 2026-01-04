import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
import urllib.parse

# ファイルパス
STATIONS_CSV = 'data/stations.csv'
STRATEGIES_CSV = 'data/strategies.csv'

def load_csv_safe(filepath):
    try:
        df = pd.read_csv(filepath, dtype=str, encoding='utf-8-sig').fillna('')
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

def clean_text(text):
    if not text: return ""
    # "1・2番線" -> "1,2" (今回は単純化のため最初の数字だけ取る)
    text = re.sub(r'\[.*?\]', '', text) # 注釈削除
    text = text.strip()
    return text

def fetch_wikipedia_platforms(station_name):
    """Wikipediaから駅の「のりば」情報を取得する"""
    print(f"  Fetching Wikipedia: {station_name}駅...")
    
    # URLエンコード
    url_name = urllib.parse.quote(f"{station_name}駅")
    url = f"https://ja.wikipedia.org/wiki/{url_name}"
    
    try:
        res = requests.get(url)
        if res.status_code != 200:
            print(f"    -> Page not found ({res.status_code})")
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 「のりば」を含むテーブルを探す
        tables = soup.find_all('table', class_='wikitable')
        platform_info = []
        
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            # 「番線」「路線」「行先」などが含まれているか簡易チェック
            if not any('番線' in h or 'のりば' in h for h in headers):
                continue
                
            # 行を解析
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                texts = [clean_text(c.get_text(strip=True)) for c in cols]
                
                # データ行の推定 (番線、路線、行先 があるはず)
                # 例: ["1", "銀座線", "渋谷方面"]
                if len(texts) >= 3:
                    # 番線っぽい数字が含まれているか
                    if re.search(r'\d', texts[0]):
                        platform_info.append({
                            'platform': texts[0],
                            'line': texts[1] if len(texts) > 1 else "",
                            'dir': texts[2] if len(texts) > 2 else ""
                        })
        
        return platform_info

    except Exception as e:
        print(f"    -> Error: {e}")
        return []

def match_platform(wiki_data, target_line, target_dir_label):
    """
    Wikiデータと、アプリの「○○方面」ラベルを突き合わせて番線を特定する
    """
    if not target_dir_label: return None
    
    # 検索キーワード作成 (例: "渋谷 方面" -> "渋谷")
    keywords = target_dir_label.replace("方面", "").strip().split('・')
    
    for info in wiki_data:
        # 路線チェック (Wikiの路線名にターゲット路線名が含まれているか、逆か)
        # 例: Wiki="東京メトロ銀座線", Target="銀座線" -> OK
        if target_line not in info['line'] and info['line'] not in target_line:
            continue
            
        # 行先チェック
        wiki_dir = info['dir']
        for kw in keywords:
            if kw in wiki_dir:
                # マッチした！
                # 番線名の整形 ("1" -> "1番線", "1・2" -> "1番線")
                raw_plat = info['platform']
                match = re.match(r'(\d+)', raw_plat)
                if match:
                    return f"{match.group(1)}番線"
                return raw_plat
                
    return None

def main():
    print("=== ホーム番線 自動補完ツール ===")
    
    # 1. データの読み込み
    df_st = load_csv_safe(STATIONS_CSV)
    df_str = load_csv_safe(STRATEGIES_CSV)
    
    if df_st.empty or df_str.empty:
        print("CSVファイルが見つかりません。")
        return

    # platform_name列がなければ追加
    if 'platform_name' not in df_str.columns:
        df_str['platform_name'] = ''

    # 駅ごとのWikiデータキャッシュ (同じ駅で何度もアクセスしないため)
    wiki_cache = {}

    # 2. strategies.csv をループして補完
    updated_count = 0
    
    for idx, row in df_str.iterrows():
        # すでに値が入っていればスキップ
        if row.get('platform_name') and row['platform_name'] != 'ホーム':
            continue
            
        line_name = row['line_name']
        station_name = row['station_name']
        direction = int(row['direction']) if row['direction'] else 1
        
        # 駅マスタから方向ラベルを取得
        st_master = df_st[
            (df_st['line_name'] == line_name) & 
            (df_st['station_name'] == station_name)
        ]
        
        if st_master.empty:
            continue
            
        # 方向ラベル (例: "渋谷 方面")
        dir_label = st_master.iloc[0]['dir_1_label'] if direction == 1 else st_master.iloc[0]['dir_m1_label']
        
        # Wikipediaからデータ取得 (キャッシュ確認)
        if station_name not in wiki_cache:
            wiki_cache[station_name] = fetch_wikipedia_platforms(station_name)
            time.sleep(1) # アクセス負荷軽減
            
        wiki_data = wiki_cache[station_name]
        
        # マッチング
        found_platform = match_platform(wiki_data, line_name, dir_label)
        
        if found_platform:
            print(f"  [Update] {line_name} {station_name} ({dir_label}) -> {found_platform}")
            df_str.at[idx, 'platform_name'] = found_platform
            updated_count += 1
        else:
            # 見つからなかった場合（Wikiの表記ゆれ等）
            # ここでデフォルトルール（fix_strategies.pyのロジック）をフォールバックとして使うのもありですが、
            # 今回は「Wikiで見つかった確実なものだけ」を更新します。
            pass

    # 3. 保存
    if updated_count > 0:
        df_str.to_csv(STRATEGIES_CSV, index=False, encoding='utf-8-sig')
        print(f"\n完了: {updated_count} 件のデータを更新しました！")
        print("generate_sql.py を実行してDBに反映してください。")
    else:
        print("\n更新対象が見つかりませんでした（または全て設定済みです）。")

if __name__ == '__main__':
    main()