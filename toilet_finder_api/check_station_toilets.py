import requests
import json
import time

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
TARGET_STATION = "大久保"  # 調べたい駅名
SEARCH_RADIUSES = [200, 500] # 調査範囲 (広すぎるとタイムアウトしやすいので絞る)

# Overpass APIのエンドポイント（メインが重いのでミラーサーバーを使用）
# 候補:
# "https://overpass.kumi.systems/api/interpreter" (高速)
# "https://lz4.overpass-api.de/api/interpreter" (公式ミラー)
OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

def get_station_location_debug(station_name):
    """ 駅の中心座標を取得し、詳細を表示する """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': f"{station_name}駅 東京都",
        'format': 'json',
        'limit': 1
    }
    headers = {'User-Agent': 'station_toilet_debugger_v2'}
    
    print(f"--- 1. 座標検索: {station_name}駅 ---")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            display_name = data[0]['display_name']
            print(f"  成功: 緯度={lat}, 経度={lon}")
            print(f"  認識された場所: {display_name}")
            # Google Mapリンク
            print(f"  [確認用] 駅の位置: https://www.google.com/maps?q={lat},{lon}")
            return lat, lon
        else:
            print("  失敗: 座標が見つかりませんでした。")
            return None, None
    except Exception as e:
        print(f"  エラー: {e}")
        return None, None

def check_osm_data(lat, lon, radius):
    """ Overpass APIで生データを取得して表示 """
    
    # タイムアウトを長めに設定 (timeout:90)
    query = f"""
    [out:json][timeout:90];
    (
      node["amenity"="toilets"](around:{radius},{lat},{lon});
      way["amenity"="toilets"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    print(f"\n--- 2. トイレデータ検索 (半径 {radius}m) ---")
    print(f"  使用サーバー: {OVERPASS_URL}")
    
    try:
        response = requests.get(OVERPASS_URL, params={'data': query}, timeout=100)
        if response.status_code != 200:
            print(f"  APIエラー: Status Code {response.status_code}")
            # エラー内容の一部を表示
            print(f"  Response: {response.text[:200]}...")
            return

        data = response.json()
        elements = data.get('elements', [])
        
        print(f"  検索結果: {len(elements)} 件ヒット")
        
        if len(elements) == 0:
            print("  -> この範囲には 'amenity=toilets' タグを持つデータがありません。")
            return

        print("\n  [詳細データ]")
        for i, el in enumerate(elements):
            e_id = el.get('id')
            tags = el.get('tags', {})
            
            # 座標
            t_lat = el.get('lat') or el.get('center', {}).get('lat')
            t_lon = el.get('lon') or el.get('center', {}).get('lon')
            
            # 名称構築
            name = tags.get('name', '名称未登録')
            operator = tags.get('operator', '')
            if operator: name += f" (運営: {operator})"
            
            desc = tags.get('description', '')
            level = tags.get('level', '')
            
            # Google Mapリンク生成
            gmap_url = f"https://www.google.com/maps?q={t_lat},{t_lon}"
            
            print(f"  {i+1}. {name}")
            print(f"     ID: {e_id}")
            print(f"     場所確認: {gmap_url}") # ★ここをクリックして場所を確認
            
            if level: print(f"     階数: {level}")
            if desc:  print(f"     説明: {desc}")
            
            # 重要なタグがあれば表示
            important_keys = ['wheelchair', 'diaper', 'changing_table', 'ostomate', 'fee', 'access', 'indoor']
            found_tags = [f"{k}={v}" for k, v in tags.items() if k in important_keys]
            if found_tags:
                print(f"     属性: {', '.join(found_tags)}")
            print("-" * 40)
            
    except Exception as e:
        print(f"  通信エラー: {e}")

def main():
    print(f"=== 駅周辺トイレデータ デバッグツール (強化版) ===")
    
    lat, lon = get_station_location_debug(TARGET_STATION)
    
    if lat and lon:
        for r in SEARCH_RADIUSES:
            check_osm_data(lat, lon, r)
            # サーバー負荷軽減のため少し待つ
            time.sleep(2) 
            
    print("\n=== 調査終了 ===")

if __name__ == "__main__":
    main()