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
TABLE_NAME = 'toilets'

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL or SUPABASE_KEY environment variables not set.")

# Supabaseクライアントの初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# -----------------------------------------------------------------
# CORS設定
# -----------------------------------------------------------------
# Vercelからのアクセスを許可するため、一時的に全許可に設定しています。
# 本番運用時は、セキュリティを高めるために特定のドメインのみ許可することをお勧めします。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 全てのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# Pydanticモデル (Supabaseのスキーマを定義)
# -----------------------------------------------------------------
class Toilet(BaseModel):
    id: str
    created_at: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    opening_hours: Optional[str] = None
    availability_notes: Optional[str] = None
    is_wheelchair_accessible: Optional[bool] = False
    has_diaper_changing_station: Optional[bool] = False
    is_ostomate_accessible: Optional[bool] = False
    is_station_toilet: Optional[bool] = False
    inside_gate: Optional[bool] = None

# 距離情報付きのレスポンスモデル
class NearestToiletResponse(Toilet):
    distance_meters: float

# -----------------------------------------------------------------
# APIエンドポイント定義
# -----------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Toilet Finder API is running!"}

@app.get("/api/toilets", response_model=List[Toilet])
async def get_toilets(
    wheelchair: bool = Query(False, description="車椅子対応のみ"),
    diaper: bool = Query(False, description="おむつ交換台ありのみ"),
    ostomate: bool = Query(False, description="オストメイト対応のみ"),
    inside_gate_filter: Optional[str] = Query(None, description="改札内フィルター (true/false)")
):
    """
    トイレデータを全件取得する (フィルタリング機能付き)
    """
    try:
        query = supabase.table(TABLE_NAME).select("*")
        
        if wheelchair:
            query = query.eq('is_wheelchair_accessible', True)
        if diaper:
            query = query.eq('has_diaper_changing_station', True)
        if ostomate:
            query = query.eq('is_ostomate_accessible', True)
        
        # 改札内/外フィルター
        if inside_gate_filter is not None:
            is_inside = inside_gate_filter.lower() == 'true'
            query = query.eq("is_station_toilet", True)
            query = query.eq("inside_gate", is_inside)

        response = query.execute()
        return response.data
    
    except Exception as e:
        print(f"Error fetching toilets: {e}")
        raise HTTPException(status_code=500, detail="データベースからのデータ取得中にエラーが発生しました")

@app.get("/api/nearest", response_model=NearestToiletResponse) 
async def get_nearest_toilet(
    lat: float = Query(..., description="ユーザーの現在地の緯度"),
    lon: float = Query(..., description="ユーザーの現在地の経度")
):
    """
    現在地から最も近いトイレを1件検索する (距離情報を付加)
    """
    try:
        # SupabaseのRPC (find_nearest_toilet) を呼び出す
        response = supabase.rpc(
            'find_nearest_toilet',
            {'user_lat': lat, 'user_lon': lon}
        ).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
             raise HTTPException(status_code=404, detail="近くにトイレが見つかりませんでした")

    except Exception as e:
        print(f"Error fetching nearest toilet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stations", response_model=List[str])
async def get_station_names():
    """
    station_platform_doors テーブルに登録されている「駅名」のユニークなリストを取得する
    """
    try:
        response = supabase.table('station_platform_doors').select('station_name').execute()
        # 重複を排除してリスト化
        station_set = set(item['station_name'] for item in response.data)
        # ソートして返す（オプション）
        return sorted(list(station_set))
    except Exception as e:
        print(f"Error fetching station names: {e}")
        raise HTTPException(status_code=500, detail="駅名リストの取得に失敗しました")

@app.get("/api/lines", response_model=List[str])
async def get_line_names(station: str = Query(..., description="駅名")):
    """
    指定された「駅名」に基づいて、「路線名」のユニークなリストを取得する
    """
    try:
        response = supabase.table('station_platform_doors').select('line_name').eq('station_name', station).execute()
        line_set = set(item['line_name'] for item in response.data)
        return sorted(list(line_set))
    except Exception as e:
        print(f"Error fetching line names: {e}")
        raise HTTPException(status_code=500, detail="路線名リストの取得に失敗しました")

@app.get("/api/train-toilet", response_model=NearestToiletResponse)
async def get_train_toilet(
    station: str = Query(..., description="駅名"),
    line: str = Query(..., description="路線名"),
    car: int = Query(..., description="号車番号")
):
    """
    指定された駅・路線・号車のドア位置から、最も近いトイレを検索する
    """
    try:
        # 1. station_platform_doors テーブルから、該当するドアの位置情報を取得
        # ★修正箇所: カラム名を door_latitude, door_longitude に変更
        door_response = supabase.table('station_platform_doors').select(
            'door_latitude, door_longitude'
        ).eq('station_name', station).eq('line_name', line).eq('car_number', car).execute()

        if not door_response.data or len(door_response.data) == 0:
             print(f"Door not found for: {station}, {line}, Car {car}")
             raise HTTPException(status_code=404, detail="指定された条件のドア位置情報が見つかりませんでした")
        
        door_location = door_response.data[0]
        # ★修正箇所: 取得したデータのキーも door_latitude, door_longitude に変更
        door_lat = door_location.get('door_latitude')
        door_lon = door_location.get('door_longitude')

        if not door_lat or not door_lon:
             raise HTTPException(status_code=500, detail="ドアの位置情報が不完全です")

        # 2. 取得したドアの緯度経度を使って、最寄りトイレ検索RPCを呼び出す
        response = supabase.rpc(
            'find_nearest_toilet',
            {'user_lat': door_lat, 'user_lon': door_lon}
        ).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
             raise HTTPException(status_code=404, detail="近くにトイレが見つかりませんでした")

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching train toilet: {e}")
        raise HTTPException(status_code=500, detail=f"乗車中検索中にエラーが発生しました: {str(e)}")