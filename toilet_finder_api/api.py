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
# 許可するオリジン（フロントエンドのURL）を設定
origins = [
    "http://localhost:3000",              # ローカル開発用
    "https://toilet-app-tau.vercel.app",  # 本番環境用（末尾の / は無し）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# Pydanticモデル
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

class NearestToiletResponse(Toilet):
    distance_meters: float

# -----------------------------------------------------------------
# APIエンドポイント
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
    try:
        query = supabase.table(TABLE_NAME).select("*")
        if wheelchair:
            query = query.eq('is_wheelchair_accessible', True)
        if diaper:
            query = query.eq('has_diaper_changing_station', True)
        if ostomate:
            query = query.eq('is_ostomate_accessible', True)
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
    lat: float = Query(..., description="緯度"),
    lon: float = Query(..., description="経度")
):
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
        print(f"Error fetching nearest toilet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 以下、乗車中検索用エンドポイント ---

@app.get("/api/lines", response_model=List[str])
async def get_all_line_names():
    """ 全ての路線名リストを取得 """
    try:
        response = supabase.table('station_platform_doors').select('line_name').execute()
        line_set = set(item['line_name'] for item in response.data if item.get('line_name'))
        return sorted(list(line_set))
    except Exception as e:
        print(f"Error fetching all line names: {e}")
        raise HTTPException(status_code=500, detail="路線名リストの取得に失敗しました")

@app.get("/api/stations-by-line", response_model=List[str])
async def get_stations_by_line(line: str = Query(..., description="路線名")):
    """ 指定された路線の駅名リストを取得 """
    try:
        response = supabase.table('station_platform_doors').select('station_name').eq('line_name', line).execute()
        station_set = set(item['station_name'] for item in response.data if item.get('station_name'))
        return sorted(list(station_set))
    except Exception as e:
        print(f"Error fetching stations for line {line}: {e}")
        raise HTTPException(status_code=500, detail="駅名リストの取得に失敗しました")

# 修正箇所のインポート部分（変更なし、確認用）
# ...

## toilet_finder_api/api.py の get_train_toilet 部分

@app.get("/api/train-toilet", response_model=Toilet) # ← レスポンス型を Toilet (距離なし) に変更
async def get_train_toilet(
    station: str = Query(..., description="駅名"),
    line: str = Query(..., description="路線名"),
    car: int = Query(..., description="号車番号")
):
    """
    指定された駅・路線・号車のドアに紐付けられた、最適なトイレを返す
    """
    try:
        # 1. ドアデータから nearest_toilet_id を取得
        door_response = supabase.table('station_platform_doors').select(
            'nearest_toilet_id'
        ).eq('station_name', station).eq('line_name', line).eq('car_number', car).maybe_single().execute()

        # データがない、または紐付けがない場合
        if not door_response.data or not door_response.data.get('nearest_toilet_id'):
             print(f"Toilet not linked for: {station}, {line}, Car {car}")
             raise HTTPException(status_code=404, detail="この場所から最適なトイレの情報がまだ登録されていません")
        
        toilet_id = door_response.data['nearest_toilet_id']

        # 2. トイレIDを使ってトイレ情報を取得
        toilet_response = supabase.table('toilets').select("*").eq('id', toilet_id).maybe_single().execute()

        if not toilet_response.data:
            raise HTTPException(status_code=404, detail="指定されたトイレの情報が見つかりませんでした")

        return toilet_response.data

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching train toilet: {e}")
        raise HTTPException(status_code=500, detail=f"検索中にエラーが発生しました: {str(e)}")