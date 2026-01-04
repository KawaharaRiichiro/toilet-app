import os
import math
import random
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

router = APIRouter(
    prefix="/commuter",
    tags=["commuter"]
)

# --- 1. 環境変数の読み込み (修正版) ---
# 実行ディレクトリに依存せず、このファイル(commuter.py)の2つ上のフォルダにある.envを探す
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# 環境変数の取得 (キー名が違っても対応できるようにORで繋ぐ)
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# --- 2. クライアント初期化 (クラッシュ回避版) ---
supabase: Optional[Client] = None

if not SUPABASE_URL or not SUPABASE_KEY:
    print("---------------------------------------------------------")
    print("Warning: .envが見つからないか、キーが設定されていません。")
    print(f"Search Path: {ENV_PATH}")
    print("★ 本番DB接続をスキップし、モックモード(ダミーデータ)で起動します。")
    print("---------------------------------------------------------")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Success: Supabase connected!")
    except Exception as e:
        print(f"Error: Supabase connection failed: {e}")
        supabase = None

# --- 型定義 ---
class ToiletOption(BaseModel):
    id: str
    stationName: str
    lineName: str = "路線情報なし"
    distanceTime: int
    totalBooths: int
    availableBooths: int
    status: str
    tags: List[str]
    lat: float
    lng: float

# --- 距離計算用ロジック ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return d

# --- APIエンドポイント ---
@router.get("/search", response_model=List[ToiletOption])
async def search_commuter_toilets(
    lat: float = Query(..., description="現在地の緯度"),
    lng: float = Query(..., description="現在地の経度")
):
    # -------------------------------------------------------
    # DB接続が成功している場合: 本番データ検索
    # -------------------------------------------------------
    if supabase:
        try:
            min_lat, max_lat = lat - 0.05, lat + 0.05
            min_lon, max_lon = lng - 0.05, lng + 0.05

            response = supabase.table("toilets") \
                .select("*") \
                .eq("is_station_toilet", True) \
                .gte("latitude", min_lat).lte("latitude", max_lat) \
                .gte("longitude", min_lon).lte("longitude", max_lon) \
                .execute()
            
            toilets_data = response.data

            # データが見つかった場合のみ処理
            if toilets_data:
                valid_options = []
                for t in toilets_data:
                    dist_km = calculate_distance(lat, lng, t["latitude"], t["longitude"])
                    
                    tags = []
                    if t.get("inside_gate"): tags.append("改札内")
                    if t.get("is_wheelchair_accessible"): tags.append("多目的あり")
                    
                    # 個室数ダミー生成
                    total_booths = random.choice([2, 3, 5, 8, 12])
                    available_booths = random.randint(0, total_booths)
                    status = "available" if available_booths > 0 else "full"
                    if available_booths == 0: status = "full"
                    elif available_booths < 2: status = "crowded"

                    time_min = int(dist_km * 3 + 2)

                    valid_options.append({
                        "data": t,
                        "dist": dist_km,
                        "formatted": ToiletOption(
                            id=str(t["id"]),
                            stationName=t.get("station_name") or t["name"],
                            lineName="JR中央線",
                            distanceTime=time_min,
                            totalBooths=total_booths,
                            availableBooths=available_booths,
                            status=status,
                            tags=tags,
                            lat=t["latitude"],
                            lng=t["longitude"]
                        )
                    })

                valid_options.sort(key=lambda x: x["dist"])
                result = [opt["formatted"] for opt in valid_options[:2]]
                
                # 2件以上あればそれを返す
                if len(result) >= 1:
                    return result

        except Exception as e:
            print(f"DB Search Error: {e} (Switching to mock data)")

    # -------------------------------------------------------
    # DB接続失敗 or データなしの場合: モックデータを返す
    # -------------------------------------------------------
    print("Returning Mock Data")
    return [
        ToiletOption(
            id="mock_a",
            stationName="四ツ谷駅(Demo)",
            lineName="中央線快速",
            distanceTime=2,
            totalBooths=3,
            availableBooths=0,
            status="full",
            tags=["ホーム階", "個室少"],
            lat=lat + 0.002, lng=lng + 0.002
        ),
        ToiletOption(
            id="mock_b",
            stationName="新宿駅(Demo)",
            lineName="中央線快速",
            distanceTime=5,
            totalBooths=15,
            availableBooths=5,
            status="available",
            tags=["南口改札内", "個室多", "TOTO"],
            lat=lat + 0.01, lng=lng + 0.01
        )
    ]