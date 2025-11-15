import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 環境変数の読み込み
load_dotenv()
# .env.local ではなく .env を読み込む場合があるため、両方チェックするか、環境変数設定に従う
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # ここは管理者権限(service_role)でもOK、またはanonキー

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in env.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# CORS設定（フロントエンドからのアクセスを許可）
origins = [
    "http://localhost:3000",
    "https://toilet-finder-web.vercel.app", # あなたのVercelのURLに書き換えてください
    # 他に許可するURLがあれば追加
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 開発中は "*" で全許可推奨（本番時はoriginsに切り替え）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- レスポンスの型定義 (Pydantic) ---
class Toilet(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    opening_hours: Optional[str] = None
    availability_notes: Optional[str] = None
    is_wheelchair_accessible: bool
    has_diaper_changing_station: bool
    is_ostomate_accessible: bool
    is_station_toilet: bool
    inside_gate: Optional[bool] = None
    
class StationMetadata(BaseModel):
    name: str

# --- エンドポイント定義 ---

@app.get("/")
def read_root():
    return {"message": "Tokyo Toilet Finder API is running!"}

# 1. 地図用：全トイレ取得 (フィルタリング付き)
@app.get("/api/toilets", response_model=List[Toilet])
async def get_toilets(
    limit: int = 5000,
    wheelchair: bool = False,
    diaper: bool = False,
    ostomate: bool = False,
    inside_gate: Optional[bool] = None
):
    query = supabase.table("toilets").select("*")

    # フィルタリング
    if wheelchair:
        query = query.eq("is_wheelchair_accessible", True)
    if diaper:
        query = query.eq("has_diaper_changing_station", True)
    if ostomate:
        query = query.eq("is_ostomate_accessible", True)
    if inside_gate is not None:
        query = query.eq("inside_gate", inside_gate)

    # 全件取得（limit指定）
    response = query.limit(limit).execute()
    return response.data

# 2. 現在地用：最寄りトイレ検索 (RPC使用)
@app.get("/api/nearest", response_model=List[Toilet])
async def get_nearest_toilets(
    lat: float,
    lng: float,
    limit: int = 20
):
    # PostGISを使ったRPC呼び出し
    response = supabase.rpc('nearby_toilets', {
        'lat': lat,
        'long': lng
    }).execute()
    
    # 必要ならここでPython側でさらにフィルタリングも可能
    # data = response.data[:limit]
    return response.data

# 3. 電車検索用：路線リスト取得
@app.get("/api/train/lines", response_model=List[str])
async def get_lines():
    # ユニークな路線名を取得したいが、Supabase JSのような .distinct() がPython版にはない場合があるため
    # 一旦全件取ってPythonで集合にするか、RPCを作るのが良い。
    # ここでは簡易的に全件取得してPythonで処理（データ量が増えると遅くなるので注意）
    response = supabase.table("station_platform_doors").select("line_name").execute()
    
    # 重複排除
    lines = sorted(list(set(item['line_name'] for item in response.data)))
    return lines

# 4. 電車検索用：駅リスト取得
@app.get("/api/train/stations", response_model=List[str])
async def get_stations(line: str):
    response = supabase.table("station_platform_doors")\
        .select("station_name")\
        .eq("line_name", line)\
        .execute()
    
    stations = sorted(list(set(item['station_name'] for item in response.data)))
    return stations

# 5. 電車検索用：方面リスト取得
@app.get("/api/train/directions", response_model=List[str])
async def get_directions(line: str, station: str):
    response = supabase.table("station_platform_doors")\
        .select("direction")\
        .eq("line_name", line)\
        .eq("station_name", station)\
        .execute()
    
    directions = sorted(list(set(item['direction'] for item in response.data if item['direction'])))
    return directions

# 6. 電車検索用：トイレ特定
@app.get("/api/train/search", response_model=Toilet)
async def search_train_toilet(
    line: str,
    station: str,
    car: int,
    direction: Optional[str] = None
):
    # ドアを特定
    query = supabase.table("station_platform_doors")\
        .select("nearest_toilet_id")\
        .eq("line_name", line)\
        .eq("station_name", station)\
        .eq("car_number", car)
    
    if direction:
        query = query.eq("direction", direction)
        
    door_res = query.maybe_single().execute()
    
    if not door_res.data:
        raise HTTPException(status_code=404, detail="Door data not found")
    
    toilet_id = door_res.data['nearest_toilet_id']
    
    # トイレ情報を取得
    toilet_res = supabase.table("toilets").select("*").eq("id", toilet_id).single().execute()
    
    if not toilet_res.data:
        raise HTTPException(status_code=404, detail="Toilet data not found")
        
    return toilet_res.data