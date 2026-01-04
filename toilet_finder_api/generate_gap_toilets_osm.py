import requests
import pandas as pd
import time
import uuid

# ---------------------------------------------------------
# 1. 収集したい自治体のリスト
# ---------------------------------------------------------
# 公式データが取り込めなかった区や、まだ未着手の市をここに書きます
TARGET_CITIES = [
    # --- 23区 (データ取得に難航していた場所) ---
    "世田谷区", "練馬区", "大田区", "杉並区", "北区", "中野区", "目黒区",
    
    # --- 多摩地域 (主要な市) ---
    "武蔵野市", "三鷹市", "調布市", "府中市", 
    "小金井市", "国分寺市", "国立市", "立川市", "八王子市", "町田市",
    "小平市", "日野市", "東村山市", "西東京市", "狛江市"
]

# ---------------------------------------------------------
# 2. Overpass API設定
# ---------------------------------------------------------
def fetch_osm_toilets_by_area(city_name):
    """ 指定した自治体名(エリア)の中にあるトイレを取得 """
    url = "http://overpass-api.de/api/interpreter"
    
    # OSMクエリ: エリア名で検索し、その中のトイレ(node/way)を取得
    query = f"""
    [out:json][timeout:30];
    area["name"="{city_name}"]["place"!="suburb"]->.searchArea;
    (
      node["amenity"="toilets"](area.searchArea);
      way["amenity"="toilets"](area.searchArea);
    );
    out center;
    """
    try:
        print(f"  検索中: {city_name} ...")
        time.sleep(2) # 負荷軽減
        resp = requests.get(url, params={'data': query}, timeout=60)
        if resp.status_code == 200:
            return resp.json().get('elements', [])
        else:
            print(f"  [Error] API Status: {resp.status_code}")
    except Exception as e:
        print(f"  [Error] {e}")
    return []

# ---------------------------------------------------------
# 3. メイン処理
# ---------------------------------------------------------
def main():
    print("=== 未対応エリアのトイレ一括収集 (OSM) ===")
    all_data = []

    for city in TARGET_CITIES:
        elements = fetch_osm_toilets_by_area(city)
        print(f"  -> {len(elements)} 件発見")

        for el in elements:
            t_lat = el.get('lat') or el.get('center', {}).get('lat')
            t_lon = el.get('lon') or el.get('center', {}).get('lon')
            if not t_lat: continue

            tags = el.get('tags', {})
            
            # 名前作成
            name = tags.get('name', f"{city}の公衆トイレ")
            if name in ['トイレ', '公衆トイレ', 'Public Toilet']:
                 name = f"{city} 公衆トイレ"

            # 住所作成（簡易的）
            address = f"東京都{city}"

            # 設備
            wheelchair = "○" if tags.get('wheelchair') == 'yes' else ""
            baby = "○" if tags.get('diaper') == 'yes' or tags.get('changing_table') == 'yes' else ""
            ostomate = "○" if tags.get('ostomate') == 'yes' else ""

            # ID生成
            unique_str = f"osm_gap_{city}_{t_lat}_{t_lon}"
            fixed_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_str))

            all_data.append({
                "id": fixed_id,
                "name": name,
                "address": address,
                "lat": t_lat,
                "lon": t_lon,
                "wheelchair": wheelchair,
                "baby_chair": baby,
                "ostomate": ostomate,
                "opening_hours": "24時間", # OSMデータは基本24時間と仮定（要確認）
                "notes": "OSMデータ(エリア検索)"
            })

    # 保存
    if all_data:
        df = pd.DataFrame(all_data)
        # 重複除外
        df = df.drop_duplicates(subset=['lat', 'lon'])
        
        output_file = "gap_toilets_osm.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n完了！ 合計 {len(df)} 件のデータを '{output_file}' に保存しました。")
    else:
        print("データが見つかりませんでした。")

if __name__ == "__main__":
    main()