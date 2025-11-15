import requests
import pandas as pd
import time
from geopy.geocoders import Nominatim

# ---------------------------------------------------------
# 1. ターゲットとなる駅リスト
# ---------------------------------------------------------
# 主要な駅を中心に検索します
TARGET_STATIONS = [
    {"line": "JR山手線", "name": "新宿"},
    {"line": "JR山手線", "name": "東京"},
    {"line": "JR山手線", "name": "渋谷"},
    {"line": "JR山手線", "name": "池袋"},
    {"line": "JR山手線", "name": "品川"},
    {"line": "JR山手線", "name": "上野"},
    {"line": "JR山手線", "name": "秋葉原"},
    {"line": "JR山手線", "name": "新橋"},
    {"line": "JR中央線", "name": "中野"},
    {"line": "JR中央線", "name": "吉祥寺"},
    {"line": "東急東横線", "name": "自由が丘"},
    {"line": "小田急線", "name": "下北沢"},
    # 必要に応じて追加してください
]

# 検索範囲（駅の中心座標からの半径メートル）
SEARCH_RADIUS = 500 

# ---------------------------------------------------------
# 2. API関数定義
# ---------------------------------------------------------
geolocator = Nominatim(user_agent="station_toilet_collector", timeout=10)

def get_station_location(station_name):
    """ 駅の中心座標を取得 """
    try:
        query = f"{station_name}駅 東京都"
        loc = geolocator.geocode(query)
        if loc:
            return loc.latitude, loc.longitude
    except:
        pass
    return None, None

def fetch_osm_toilets(lat, lon, radius):
    """ Overpass APIを使って周辺のトイレデータを取得 """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # OSMクエリ: 指定座標周辺の amenity=toilets を取得
    query = f"""
    [out:json];
    (
      node["amenity"="toilets"](around:{radius},{lat},{lon});
      way["amenity"="toilets"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': query}, timeout=30)
        response.raise_for_status()
        return response.json().get('elements', [])
    except Exception as e:
        print(f"  [Error] API Request failed: {e}")
        return []

# ---------------------------------------------------------
# 3. メイン処理
# ---------------------------------------------------------
def main():
    print("=== OpenStreetMapを使った駅トイレ収集を開始します ===")
    all_toilets = []

    for station in TARGET_STATIONS:
        s_name = station["name"]
        line = station["line"]
        
        print(f"\n■ {s_name}駅 ({line}) を検索中...")
        
        # 1. 駅の座標を取得
        lat, lon = get_station_location(s_name)
        if not lat:
            print("  -> 駅の場所が見つかりませんでした。スキップします。")
            continue
            
        # 2. OSMからトイレデータを取得
        elements = fetch_osm_toilets(lat, lon, SEARCH_RADIUS)
        print(f"  -> {len(elements)} 件のトイレデータを発見しました。")
        
        for el in elements:
            # 座標の取得 (nodeならlat/lon, wayならcenterのlat/lon)
            t_lat = el.get('lat') or el.get('center', {}).get('lat')
            t_lon = el.get('lon') or el.get('center', {}).get('lon')
            
            if not t_lat: continue

            tags = el.get('tags', {})
            
            # 属性情報の抽出
            wheelchair = tags.get('wheelchair') == 'yes'
            diaper = tags.get('diaper') == 'yes' or tags.get('changing_table') == 'yes'
            # OSMにはオストメイトタグ(ostomate=yes)がある場合も
            ostomate = tags.get('ostomate') == 'yes' 
            
            # 名前があれば使う、なければ「〇〇駅付近のトイレ」
            t_name = tags.get('name', f"{s_name}駅周辺のトイレ")
            
            # レベル（階数）情報
            level = tags.get('level', '')
            if level: t_name += f" ({level}階)"

            # データ生成
            row = {
                "station_name": s_name, # 所属駅
                "toilet_name": t_name,  # トイレ名
                "lat": t_lat,
                "lon": t_lon,
                "wheelchair": "○" if wheelchair else "",
                "baby": "○" if diaper else "",
                "ostomate": "○" if ostomate else "",
                "note": "OpenStreetMapデータ"
            }
            all_toilets.append(row)
        
        time.sleep(2) # APIへの負荷軽減

    # CSV保存
    if all_toilets:
        df = pd.DataFrame(all_toilets)
        # 重複排除（同じIDのトイレが取れることがあるため座標で簡易重複除外）
        df = df.drop_duplicates(subset=['lat', 'lon'])
        
        filename = "station_toilet_osm.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n完了！ 合計 {len(df)} 件のデータを '{filename}' に保存しました。")
        print("※ このファイルの中身を確認し、不要なデータ（駅の外の公園トイレなど）があれば行を削除してください。")
    else:
        print("\nデータが見つかりませんでした。")

if __name__ == "__main__":
    main()