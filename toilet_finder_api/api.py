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

# --- ここから追加 ---
# 許可するオリジン（フロントエンドのURL）を設定
origins = [
    "http://localhost:3000",               # ローカル開発用
    "https://toilet-app-tau.vercel.app/

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 全てのHTTPメソッドを許可（GET, POSTなど）
    allow_headers=["*"],  # 全てのヘッダーを許可
)
# --- ここまで追加 ---

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
    
    # 駅トイレ関連カラム
    is_station_toilet: Optional[bool] = False
    station_name: Optional[str] = None
    inside_gate: Optional[bool] = None
    
    average_rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    last_synced_at: Optional[str] = None

# 最寄り検索APIの応答用モデル (距離情報を含む)
class NearestToiletResponse(Toilet):
    distance_meters: float

# -----------------------------------------------------------------
# 既存のAPIエンドポイント
# -----------------------------------------------------------------

@app.get("/api/toilets", response_model=List[Toilet])
async def get_all_toilets(
    wheelchair: Optional[bool] = Query(None, description="車椅子対応でフィルタ"),
    diaper: Optional[bool] = Query(None, description="おむつ交換台でフィルタ"),
    ostomate: Optional[bool] = Query(None, description="オストメイト対応でフィルタ"),
    inside_gate_filter: Optional[bool] = Query(None, description="改札内(True)または改札外(False)でフィルタ")
):
    """
    全トイレデータを取得し、オプションでフィルタリングする
    """
    try:
        query = supabase.table(TABLE_NAME).select("*")

        if wheelchair is not None:
            query = query.eq("is_wheelchair_accessible", wheelchair)
        if diaper is not None:
            query = query.eq("has_diaper_changing_station", diaper)
        if ostomate is not None:
            query = query.eq("is_ostomate_accessible", ostomate)
        
        if inside_gate_filter is not None:
            query = query.eq("is_station_toilet", True)
            query = query.eq("inside_gate", inside_gate_filter)

        response = query.execute()
        return response.data
    
    except Exception as e:
        print(f"Error fetching toilets: {e}")
        raise HTTPException(status_code=500, detail="データベースからのデータ取得中にエラーが発生しました")

# -----------------------------------------------------------------
# 最寄り検索エンドポイント (距離情報対応)
# -----------------------------------------------------------------

@app.get("/api/nearest", response_model=NearestToiletResponse) 
async def get_nearest_toilet(
    lat: float = Query(..., description="ユーザーの現在地の緯度"),
    lon: float = Query(..., description="ユーザーの現在地の経度")
):
    """
    現在地から最も近いトイレを1件検索する (距離情報を付加)
    """
    try:
        response = supabase.rpc(
            'find_nearest_toilet',
            {'user_lat': lat, 'user_lon': lon}
        ).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="近くにトイレが見つかりませんでした")

    except Exception as e:
        print(f"Error calling RPC: {e}")
        raise HTTPException(status_code=500, detail="最寄りトイレの検索中にサーバーエラーが発生しました")

# -----------------------------------------------------------------
# ★★★ 新規追加: 電車内検索のエンドポイント ★★★
# -----------------------------------------------------------------

@app.get("/api/in-train-search", response_model=NearestToiletResponse)
async def get_in_train_search(
    station: str = Query(..., description="駅名 (例: 上野駅)"),
    line: str = Query(..., description="路線名 (例: 山手線内回り)"),
    car: int = Query(..., description="車両番号 (例: 5)")
):
    """
    駅名、路線、車両番号からドアの座標を特定し、
    そのドアから最も近いトイレを1件検索する
    """
    try:
        # 1. station_platform_doors テーブルから「ドアの座標」を検索
        door_response = supabase.table('station_platform_doors').select(
            'door_latitude, door_longitude'
        ).eq(
            'station_name', station
        ).eq(
            'line_name', line
        ).eq(
            'car_number', car
        ).execute()

        if not door_response.data:
            raise HTTPException(status_code=404, detail="指定された電車のドア情報が見つかりません。")

        door_data = door_response.data[0]
        door_lat = door_data['door_latitude']
        door_lon = door_data['door_longitude']

        # 2. 取得した「ドアの座標」を使って、既存の「最寄りトイレ検索RPC」を呼び出す
        toilet_response = supabase.rpc(
            'find_nearest_toilet',
            {'user_lat': door_lat, 'user_lon': door_lon}
        ).execute()

        if toilet_response.data and len(toilet_response.data) > 0:
            return toilet_response.data[0]
        else:
            raise HTTPException(status_code=404, detail="ドアの近くにトイレが見つかりませんでした")

    except Exception as e:
        print(f"Error calling in-train search: {e}")
        raise HTTPException(status_code=500, detail="電車内検索中にサーバーエラーが発生しました")

# -----------------------------------------------------------------
# ★★★ 新規追加: 駅名リスト取得のエンドポイント (安全版) ★★★
# -----------------------------------------------------------------

@app.get("/api/stations", response_model=List[str])
async def get_station_names():
    """
    station_platform_doors テーブルに登録されている「駅名」の
    ユニークなリストを取得する (Python側で重複排除)
    """
    try:
        # まず全データを取得
        response = supabase.table('station_platform_doors').select(
            'station_name'
        ).execute()
        
        # Python側で重複を排除
        station_set = set(item['station_name'] for item in response.data)
        return list(station_set)
    
    except Exception as e:
        print(f"Error fetching station names: {e}")
        raise HTTPException(status_code=500, detail="駅名リストの取得に失敗しました")

# -----------------------------------------------------------------
# ★★★ 新規追加: 路線名リスト取得のエンドポイント (安全版) ★★★
# -----------------------------------------------------------------

@app.get("/api/lines", response_model=List[str])
async def get_line_names(
    station: str = Query(..., description="駅名")
):
    """
    指定された「駅名」に基づいて、「路線名」の
    ユニークなリストを取得する (Python側で重複排除)
    """
    try:
        # まず指定された駅名で絞り込む
        response = supabase.table('station_platform_doors').select(
            'line_name'
        ).eq('station_name', station).execute()
        
        # Python側で重複を排除
        line_set = set(item['line_name'] for item in response.data)
        return list(line_set)
    
    except Exception as e:
        print(f"Error fetching line names: {e}")
        raise HTTPException(status_code=500, detail="路線名リストの取得に失敗しました")