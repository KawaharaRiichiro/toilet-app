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
    # Render等の環境変数で設定されている場合はエラーにしない
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
    # 必要に応じて追加
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 開発中は全許可推奨
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
    is_wheelchair_accessible: bool
    has_diaper_changing_station: bool
    is_ostomate_accessible: bool
    is_station_toilet: bool
    inside_gate: Optional[bool] = None
    distance: Optional[float] = None # 将来的にAPIで距離計算する場合用

# -----------------------------------------------------------------
# APIエンドポイント
# -----------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Tokyo Toilet Finder API is running!"}

# 1. 地図用：全トイレ取得 (フィルタリング付き)
@app.get("/api/toilets", response_model=List[Toilet])
async def get_toilets(
    limit: int = 5000, # ★デフォルト5000件に設定
    wheelchair: bool = False,
    diaper: bool = False,
    ostomate: bool = False,
    inside_gate: Optional[bool] = None
):
    query = supabase.table("toilets").select("*")

    if wheelchair:
        query = query.eq("is_wheelchair_accessible", True)
    if diaper:
        query = query.eq("has_diaper_changing_station", True)
    if ostomate:
        query = query.eq("is_ostomate_accessible", True)
    if inside_gate is not None:
        query = query.eq("inside_gate", inside_gate)

    response = query.limit(limit).execute()
    return response.data

# 2. 現在地用：最寄りトイレ検索
@app.get("/api/nearest", response_model=List[Toilet])
async def get_nearest_toilets(
    lat: float,
    lng: float,
    limit: int = 200 # ★デフォルト200件に増量
):
    # PostGISを使ったRPC呼び出し
    response = supabase.rpc('nearby_toilets', {
        'lat': lat,
        'long': lng
    }).execute()
    
    # 取得したデータをlimit件数で切る
    data = response.data
    if limit and len(data) > limit:
        data = data[:limit]

    return data

# 3. 電車検索用：路線リスト取得
@app.get("/api/train/lines", response_model=List[str])
async def get_lines():
    response = supabase.table("station_platform_doors").select("line_name").execute()
    # 重複排除してソート
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

# 6. 電車検索用：トイレ特定 (方面対応版)
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
    
    # 方面が指定されていれば条件に追加
    if direction:
        query = query.eq("direction", direction)
        
    door_res = query.maybe_single().execute()
    
    if not door_res.data or not door_res.data.get('nearest_toilet_id'):
        raise HTTPException(status_code=404, detail="この場所の情報はまだ登録されていません")
    
    toilet_id = door_res.data['nearest_toilet_id']
    
    # トイレ情報を取得
    toilet_res = supabase.table("toilets").select("*").eq("id", toilet_id).single().execute()
    
    if not toilet_res.data:
        raise HTTPException(status_code=404, detail="トイレデータが見つかりません")
        
    return toilet_res.data