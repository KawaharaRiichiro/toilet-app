import requests
import pandas as pd
import time
import uuid
import os
import json
import sys
from dotenv import load_dotenv

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
STATIONS_CSV = 'data/stations.csv'
OUTPUT_CSV = 'station_toilet.csv'
SEARCH_RADIUS = 500

# Overpass APIのエンドポイント
OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

# リトライ設定
MAX_RETRIES = 3
RETRY_DELAY = 5 

# Gemini API設定
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
USE_GEMINI = False 

if GEMINI_API_KEY:
    USE_GEMINI = True
    print("Gemini API: 有効 (REST APIモード)")
else:
    print("Gemini API: 無効 (APIキーが設定されていません)")

def generate_route_guide(line_name, station_name, toilet_name, floor, features):
    """ Gemini APIを使ってトイレへの案内文を生成する (モデル自動切替版) """
    if not USE_GEMINI:
        return f"{station_name}駅周辺のトイレ情報です。"

    # 試行するモデルのリスト (優先順)
    models_to_try = [
        "gemini-1.5-flash", 
        "gemini-1.5-flash-latest", 
        "gemini-1.0-pro"
    ]

    prompt = f"""
    あなたは親切な駅員です。以下の情報をもとに、駅のホームからトイレへの行き方を推測して、簡潔で分かりやすい案内文（100文字以内）を作成してください。
    
    条件:
    - 駅名: {station_name}駅
    - 路線: {line_name}
    - トイレの場所: {toilet_name}
    - 階数: {floor if floor else "不明"}
    - 特徴: {features}
    
    もし情報が少なくて推測できない場合は、「{station_name}駅の係員にお尋ねください。」のような無難な案内にして、嘘の道順は書かないでください。
    トーン: 丁寧語で、急いでいる人に配慮した簡潔さ。
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        try:
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and data['candidates']:
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    return text.replace("\n", " ")
                else:
                    return f"{station_name}駅周辺のトイレ情報です。"
            
            elif response.status_code == 404:
                # モデルが見つからない場合は次のモデルを試す
                # print(f"  [Info] Model {model_name} not found, trying next...")
                continue
            
            elif response.status_code == 429:
                print("  [Gemini] Rate limit exceeded. Using default text.")
                return f"{station_name}駅周辺のトイレ情報です。"
                
            else:
                print(f"  [Gemini Error] {response.status_code}: {response.text[:50]}...")
                return f"{station_name}駅周辺のトイレ情報です。"

        except Exception as e:
            print(f"  [Gemini Error] {e}")
            continue

    # 全モデル失敗時
    return f"{station_name}駅周辺のトイレ情報です。"

def load_target_stations():
    """ stations.csv から検索対象の駅リストを読み込む """
    if not os.path.exists(STATIONS_CSV):
        print(f"Error: {STATIONS_CSV} が見つかりません。")
        return [
            {"line_name": "JR山手線", "station_name": "新宿"},
            {"line_name": "JR山手線", "station_name": "渋谷"},
            {"line_name": "JR山手線", "station_name": "東京"},
        ]
    
    try:
        df = pd.read_csv(STATIONS_CSV, dtype=str).fillna('')
        if 'station_name' not in df.columns or 'line_name' not in df.columns:
            print("Error: stations.csv に必要なカラム(station_name, line_name)がありません。")
            return []
        
        targets = df[['line_name', 'station_name']].to_dict('records')
        return targets
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

def get_station_location(station_name):
    """ 駅の中心座標を取得 (Nominatim API) """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': f"{station_name}駅 東京都",
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'station_toilet_collector_v6_robust'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return float(data[0]['lat']), float(data[0]['lon'])
            return None, None
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            pass
    return None, None

def fetch_osm_toilets(lat, lon, radius):
    """ Overpass APIでトイレデータを取得 """
    query = f"""
    [out:json][timeout:90];
    (
      node["amenity"="toilets"](around:{radius},{lat},{lon});
      way["amenity"="toilets"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(OVERPASS_URL, params={'data': query}, timeout=100)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return data.get('elements', [])
                except ValueError:
                    print(f"  [Error] Invalid JSON response.")
                    return []
            
            if response.status_code in [429, 500, 502, 503, 504]:
                print(f"  [Retry {attempt+1}/{MAX_RETRIES}] Server Busy ({response.status_code}). Waiting...")
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            else:
                print(f"  [Error] API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  [Error] Connection failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return []
    
    return []

def main():
    print("=== トイレデータ収集開始 (堅牢版) ===")
    
    targets = load_target_stations()
    print(f"対象: {len(targets)} 件の駅データ")
    
    all_toilets = []
    processed_stations = {}

    try:
        for i, station in enumerate(targets):
            s_name = station["station_name"]
            l_name = station["line_name"]
            
            print(f"[{i+1}/{len(targets)}] {s_name} ({l_name})...", end=" ", flush=True)
            
            if s_name in processed_stations:
                lat, lon = processed_stations[s_name]
            else:
                lat, lon = get_station_location(s_name)
                if lat:
                    processed_stations[s_name] = (lat, lon)
                time.sleep(1.2)
            
            if not lat:
                print("座標不明 -> Skip")
                continue

            elements = fetch_osm_toilets(lat, lon, SEARCH_RADIUS)
            print(f"発見: {len(elements)}件")
            
            for el in elements:
                t_lat = el.get('lat') or el.get('center', {}).get('lat')
                t_lon = el.get('lon') or el.get('center', {}).get('lon')
                if not t_lat: continue

                tags = el.get('tags', {})
                
                wheelchair = "○" if tags.get('wheelchair') == 'yes' else ""
                baby_chair = "○" if (tags.get('diaper') == 'yes' or tags.get('changing_table') == 'yes') else ""
                ostomate = "○" if tags.get('ostomate') == 'yes' else ""
                
                t_name = tags.get('name', '駅周辺トイレ')
                level = tags.get('level', '')
                floor = f"{level}階" if level else ""
                
                base_note = t_name
                if tags.get('fee') == 'yes': base_note += " (有料)"
                if tags.get('access') == 'customers': base_note += " (店舗客用)"

                # 特徴リスト作成
                feat_list = []
                if wheelchair: feat_list.append("車椅子対応")
                if baby_chair: feat_list.append("ベビーチェア/シート")
                if ostomate: feat_list.append("オストメイト")
                if tags.get('fee') == 'yes': feat_list.append("有料")
                features_str = ", ".join(feat_list) if feat_list else "特になし"
                
                # Geminiで案内文生成
                gemini_note = ""
                if USE_GEMINI:
                    print("  [Gemini] 生成中...", end="", flush=True)
                    gemini_note = generate_route_guide(l_name, s_name, t_name, floor, features_str)
                    print("完了")
                    # 無料枠の制限(15RPM)を考慮して待機。
                    # ここを短くしすぎると429エラーになります。
                    time.sleep(4) 
                
                final_note = f"{gemini_note} ({base_note})" if gemini_note else base_note
                
                row = {
                    "id": str(uuid.uuid4()),
                    "line_name": l_name,
                    "station_name": s_name,
                    "toilet_name": t_name,
                    "lat": t_lat,
                    "lng": t_lon,
                    "floor": floor,
                    "wheelchair": wheelchair,
                    "baby_chair": baby_chair,
                    "ostomate": ostomate,
                    "notes": final_note,
                    "platform_name": ""
                }
                all_toilets.append(row)
            
            # 通常待機
            time.sleep(1) 

    except KeyboardInterrupt:
        print("\n\nユーザーによる中断。ここまでのデータを保存します...")
    except Exception as e:
        print(f"\n\n予期せぬエラー: {e}")
        print("ここまでのデータを保存します...")

    # CSV保存 (中断時も実行される)
    if all_toilets:
        df = pd.DataFrame(all_toilets)
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\n完了: {OUTPUT_CSV} に {len(df)} 件保存しました。")
    else:
        print("\nデータが見つかりませんでした。")

if __name__ == "__main__":
    main()