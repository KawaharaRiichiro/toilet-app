import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# .envファイルから環境変数を読み込む
load_dotenv()

# Supabaseの接続情報
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in .env file.")

# Supabaseクライアントの初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# -----------------------------------------------------------------
# CORS設定
# -----------------------------------------------------------------
origins = [
    "http://localhost:3000",
    "https://toilet-finder-web.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 開発中は全許可推奨なら ["*"] に変更
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# Pydanticモデル定義 (レスポンスの型)
# -----------------------------------------------------------------
class Toilet(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    opening_hours: Optional[str] = None
    availability_notes: Optional[str] = None
    is_wheelchair_accessible: Optional[bool] = False
    has_diaper_changing_station: Optional[bool] = False
    is_ostomate_accessible: Optional[bool] = False
    is_station_toilet: bool = False
    station_name: Optional[str] = None
    inside_gate: Optional[bool] = None

# -----------------------------------------------------------------
# エンドポイント定義
# -----------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Toilet Finder API is running!"}

# 1. 周辺トイレ検索
@app.get("/toilets/nearby", response_model=List[dict])
def get_nearby_toilets(lat: float, lng: float):
    try:
        response = supabase.rpc("nearby_toilets", {"lat": lat, "long": lng}).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching nearby toilets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 電車内検索用API群 ---

# 2. 路線一覧取得
@app.get("/api/train/lines", response_model=List[str])
def get_lines():
    try:
        response = supabase.table("station_platform_doors").select("line_name").execute()
        if not response.data: return []
        # 重複排除してソート
        lines = sorted(list(set(item['line_name'] for item in response.data)))
        return lines
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. 駅一覧取得
@app.get("/api/train/stations", response_model=List[str])
def get_stations(line: str):
    try:
        response = supabase.table("station_platform_doors").select("station_name").eq("line_name", line).execute()
        if not response.data: return []
        stations = sorted(list(set(item['station_name'] for item in response.data)))
        return stations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. 【新規】方面一覧取得
@app.get("/api/train/directions", response_model=List[str])
def get_directions(line: str, station: str):
    try:
        response = supabase.table("station_platform_doors")\
            .select("direction")\
            .eq("line_name", line)\
            .eq("station_name", station)\
            .execute()
        if not response.data: return []
        # 重複排除してソート (例: ["内回り", "外回り"])
        directions = sorted(list(set(item['direction'] for item in response.data if item['direction'])))
        return directions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. 【新規】号車一覧取得
@app.get("/api/train/cars", response_model=List[int])
def get_cars(line: str, station: str, direction: str):
    try:
        response = supabase.table("station_platform_doors")\
            .select("car_number")\
            .eq("line_name", line)\
            .eq("station_name", station)\
            .eq("direction", direction)\
            .execute()
        if not response.data: return []
        # 重複排除してソート (例: [1, 2, ..., 11])
        cars = sorted(list(set(item['car_number'] for item in response.data)))
        return cars
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. 【新規】最適なトイレを1つ特定する
@app.get("/api/train/search", response_model=Toilet)
def search_train_toilet(line: str, station: str, direction: str, car: int):
    try:
        # 1. 条件に合うドアを探す（複数ある場合は door_number が小さいもの＝ホーム端などを優先してもよいが、今回は1件取得）
        door_res = supabase.table("station_platform_doors")\
            .select("nearest_toilet_id")\
            .eq("line_name", line)\
            .eq("station_name", station)\
            .eq("direction", direction)\
            .eq("car_number", car)\
            .limit(1)\
            .execute()
        
        if not door_res.data or not door_res.data[0].get('nearest_toilet_id'):
            raise HTTPException(status_code=404, detail="トイレ情報が見つかりません")
            
        toilet_id = door_res.data[0]['nearest_toilet_id']

        # 2. トイレ情報を取得
        toilet_res = supabase.table("toilets").select("*").eq("id", toilet_id).single().execute()
        
        if not toilet_res.data:
            raise HTTPException(status_code=404, detail="トイレデータが存在しません")
            
        return toilet_res.data

    except Exception as e:
        print(f"Search Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)