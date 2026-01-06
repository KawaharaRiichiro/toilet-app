import os
from typing import List, Optional
from datetime import datetime, time, timedelta
import math
from fastapi import FastAPI, HTTPException, Query, Body, Depends
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import traceback

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# クライアント初期化
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY is missing.")
    
supabase: Client = create_client(SUPABASE_URL or "", SUPABASE_KEY or "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# 型定義
# -----------------------------------------------------------------

class PredictionResult(BaseModel):
    station_id: str
    station_name: str
    stop_order: int
    walking_cars: float
    target_car: float
    facility_type: str
    crowd_level: int = Field(default=3, description="混雑度(デフォルト3)")
    realtime_crowd_level: Optional[float] = Field(default=None, description="リアルタイム混雑度(ユーザー投稿平均)")
    notes: Optional[str] = Field(default=None)
    toilet_name: Optional[str] = Field(default=None, description="トイレの具体的な名称")
    platform_name: str = Field(default="ホーム", description="発着番線")
    message: str
    latitude: Optional[float] = Field(default=None, description="目的地緯度")
    longitude: Optional[float] = Field(default=None, description="目的地経度")
    location_type: str = Field(default="station", description="位置情報の精度")
    toilet_id: Optional[str] = Field(default=None, description="トイレID")

class LineInfo(BaseModel):
    id: str
    name: str
    color: str
    direction_1_name: str
    direction_minus_1_name: str
    max_cars: int = Field(default=10, description="最大号車数")

class CongestionReport(BaseModel):
    toilet_id: str
    congestion_level: int = Field(..., ge=1, le=3, description="1:空き, 2:普通, 3:混雑")
    user_id: Optional[str] = None 

# -----------------------------------------------------------------
# ヘルパー関数
# -----------------------------------------------------------------

def safe_float(value, default=0.0):
    try:
        if value is None: return default
        if isinstance(value, str) and not value.strip(): return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        if value is None: return default
        if isinstance(value, str) and not value.strip(): return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def is_time_available(time_str: str) -> bool:
    if not time_str or time_str == "ALL": return True
    try:
        now = datetime.now().time()
        for r in str(time_str).split(','):
            parts = r.split('-')
            if len(parts) != 2: continue
            start, end = parts
            s_time = datetime.strptime(start.strip(), "%H:%M").time()
            e_time = datetime.strptime(end.strip(), "%H:%M").time()
            if s_time <= e_time:
                if s_time <= now <= e_time: return True
            else:
                if s_time <= now or now <= e_time: return True
    except:
        return True
    return False

def format_facility(fac_code: str) -> str:
    if not fac_code: return "不明"
    parts = str(fac_code).split(',')
    labels = []
    for p in parts:
        p = p.strip()
        if p == 'stairs': labels.append("階段")
        elif p == 'escalator': labels.append("エスカレーター")
        elif p == 'elevator': labels.append("エレベーター")
        elif p == '調査中': labels.append("調査中")
        else: labels.append(p)
    return "・".join(labels)

def get_line_terminals(line_id: str):
    try:
        res_max = supabase.table("line_stations")\
            .select("station_order, stations!line_stations_station_id_fkey(name)")\
            .eq("line_id", line_id)\
            .order("station_order", desc=True)\
            .limit(1).execute()
        res_min = supabase.table("line_stations")\
            .select("station_order, stations!line_stations_station_id_fkey(name)")\
            .eq("line_id", line_id)\
            .order("station_order", desc=False)\
            .limit(1).execute()
        
        term_1 = "下り方面"
        term_m1 = "上り方面"
        
        if res_max.data and len(res_max.data) > 0 and res_max.data[0].get('stations'):
            term_1 = str(res_max.data[0]['stations'].get('name', '')) + " 方面"
        
        if res_min.data and len(res_min.data) > 0 and res_min.data[0].get('stations'):
            term_m1 = str(res_min.data[0]['stations'].get('name', '')) + " 方面"
            
        return term_1, term_m1
    except Exception as e:
        print(f"[Warn] Terminal lookup failed: {e}")
        return "方面1", "方面2"

# -----------------------------------------------------------------
# API実装
# -----------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Toilet Finder API is running!"}

@app.get("/lines", response_model=List[LineInfo])
def get_lines(lat: Optional[float] = None, lng: Optional[float] = None):
    try:
        # 全路線データを取得（キャッシュとして利用）
        all_lines = supabase.table("lines").select("*").execute().data
        
        target_line_ids = set()
        
        # 緯度経度が指定されている場合、最寄り駅を特定する
        if lat is not None and lng is not None:
            try:
                # 全駅の座標を取得
                all_stations = supabase.table("stations").select("id, lat, lng").execute().data
                
                nearest_station_id = None
                min_dist_sq = float('inf') # 距離の二乗で比較
                
                for st in all_stations:
                    s_lat = safe_float(st.get('lat') or st.get('latitude'))
                    s_lng = safe_float(st.get('lng') or st.get('lon') or st.get('longitude'))
                    
                    if s_lat != 0 and s_lng != 0:
                        # 三平方の定理で距離の二乗を計算（ルート計算を省いて高速化）
                        dist_sq = (s_lat - lat)**2 + (s_lng - lng)**2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            nearest_station_id = st['id']
                
                # 最寄り駅が見つかった場合、その駅を通る路線IDを取得
                # 0.01 (約11km圏内) くらいを安全弁としておく
                if nearest_station_id and min_dist_sq < 0.01:
                    ls_res = supabase.table("line_stations").select("line_id").eq("station_id", nearest_station_id).execute()
                    for item in ls_res.data:
                        target_line_ids.add(item['line_id'])
                else:
                    # 近くに駅がない場合（海外など）は空リストを返す
                    return []

            except Exception as e:
                print(f"[Warning] Nearest station search error: {e}")
                # エラー時は空リスト（何も表示しない）
                return []

        # 結果の構築
        result_lines = []
        
        for line in all_lines:
            # 位置情報フィルタが有効で、かつ対象外の路線ならスキップ
            if lat is not None and lng is not None:
                if line['id'] not in target_line_ids:
                    continue
            
            term_1, term_m1 = get_line_terminals(line['id'])
            max_cars = safe_int(line.get('max_cars'), 10)
            
            result_lines.append({
                "id": line['id'], 
                "name": line['name'], 
                "color": line['color'],
                "direction_1_name": term_1, 
                "direction_minus_1_name": term_m1,
                "max_cars": max_cars
            })
        
        return result_lines

    except Exception as e:
        print(f"[Error] /lines failed: {e}")
        return []

@app.get("/stations", response_model=List[dict])
def get_stations(line_id: str):
    patterns = [
        "station_order, dir_1_label, dir_m1_label, stations!line_stations_station_id_fkey(id, name, lat, lng)",
        "station_order, stations!line_stations_station_id_fkey(id, name, lat, lng)",
        "station_order, stations!line_stations_station_id_fkey(id, name)" 
    ]
    res = None
    for pattern in patterns:
        try:
            r = supabase.table("line_stations").select(pattern).eq("line_id", line_id).order("station_order").execute()
            res = r
            if r.data: break
        except Exception: continue
    
    if not res or not res.data:
        raise HTTPException(status_code=500, detail="DB Error: Stations not found")

    stations = []
    for item in res.data:
        st = item.get('stations')
        if not st: continue
        s_lat = safe_float(st.get('lat') or st.get('latitude'))
        s_lng = safe_float(st.get('lng') or st.get('lon') or st.get('longitude'))
        stations.append({
            "id": st['id'], "name": st['name'], "order": item['station_order'],
            "lat": s_lat, "lng": s_lng,
            "dir_1_label": item.get('dir_1_label'), "dir_m1_label": item.get('dir_m1_label')
        })
    return stations

@app.get("/predict", response_model=List[PredictionResult])
def predict_best_station(line_id: str, current_station_id: str, user_car: int, direction: int = Query(1)):
    try:
        try:
            current_link_res = supabase.table("line_stations").select("*").eq("line_id", line_id).eq("station_id", current_station_id).single().execute()
        except Exception:
            raise HTTPException(status_code=500, detail="Database Error: Current station fetch failed")

        if not current_link_res.data:
            raise HTTPException(status_code=404, detail="Current station not found")
        
        current_link = current_link_res.data
        
        target_ids = []
        target_ids.append({'id': current_station_id, 'stop_order': 0})
        
        if direction == 1:
            n1 = current_link.get('dir_1_next_station_id')
            n2 = current_link.get('dir_1_next_next_station_id')
            if n1: target_ids.append({'id': n1, 'stop_order': 1})
            if n2: target_ids.append({'id': n2, 'stop_order': 2})
        else:
            n1 = current_link.get('dir_m1_next_station_id')
            n2 = current_link.get('dir_m1_next_next_station_id')
            if n1: target_ids.append({'id': n1, 'stop_order': 1})
            if n2: target_ids.append({'id': n2, 'stop_order': 2})

        results = []
        
        for target in target_ids:
            try:
                st_res = supabase.table("stations").select("id, name, lat, lng").eq("id", target['id']).single().execute()
                if not st_res.data: continue
                st_data = st_res.data
                
                dest_lat = safe_float(st_data.get('lat'))
                dest_lng = safe_float(st_data.get('lng'))
                location_type = "station"
                
                strategies = []
                try:
                    strategies_res = supabase.table("toilet_strategies").select("*").eq("station_id", st_data['id']).eq("direction", direction).execute()
                    strategies = strategies_res.data if strategies_res.data else []
                except Exception:
                    strategies = []

                best_cand = None
                min_dist = 999.0
                
                for cand in strategies:
                    if not is_time_available(str(cand.get('available_time', 'ALL'))): 
                        continue
                    
                    raw_pos = cand.get('car_pos') or cand.get('target_car_number')
                    tgt = safe_float(raw_pos, 0.0)
                    
                    dist = abs(user_car - tgt)
                    if dist < min_dist:
                        min_dist = dist
                        best_cand = cand
                
                wc, tc, fac, crd, msg = 99.0, 1.0, "調査中", 3, ""
                realtime_crowd = None
                notes = ""
                toilet_name = None
                platform = "ホーム"
                toilet_id = None
                
                if best_cand:
                    raw_tc = best_cand.get('car_pos') or best_cand.get('target_car_number')
                    tc = safe_float(raw_tc, 1.0)
                    wc = min_dist
                    fac = format_facility(str(best_cand.get('facility_type', '')))
                    crd = safe_int(best_cand.get('crowd_level'), 3)
                    notes = str(best_cand.get('route_memo') or best_cand.get('notes') or '')
                    raw_platform = best_cand.get('platform_name')
                    platform = str(raw_platform) if raw_platform else "ホーム"
                    toilet_id = best_cand.get('target_toilet_id')
                    
                    if toilet_id:
                        try:
                            t_res = supabase.table("toilets").select("lat, lng, name").eq("id", toilet_id).single().execute()
                            if t_res.data:
                                t_lat = safe_float(t_res.data.get('lat'))
                                t_lng = safe_float(t_res.data.get('lng'))
                                toilet_name = t_res.data.get('name')
                                if t_lat != 0 and t_lng != 0:
                                    dest_lat = t_lat
                                    dest_lng = t_lng
                                    location_type = "exact"
                            
                            reports = supabase.table("congestion_reports") \
                                .select("congestion_level") \
                                .eq("toilet_id", toilet_id) \
                                .order("reported_at", desc=True) \
                                .limit(5) \
                                .execute()
                            
                            if reports.data:
                                levels = [r['congestion_level'] for r in reports.data]
                                realtime_crowd = sum(levels) / len(levels)
                                
                        except Exception as e:
                            pass

                if wc < 0.5: msg = "降りてすぐ目の前！"
                elif wc <= 2.0: msg = "かなり近いです"
                else: msg = f"{wc:.1f}両分歩きます"
                
                if dest_lat == 0: dest_lat = None
                if dest_lng == 0: dest_lng = None

                results.append({
                    "station_id": st_data['id'],
                    "station_name": st_data['name'],
                    "stop_order": target['stop_order'],
                    "walking_cars": round(wc, 1),
                    "target_car": tc,
                    "facility_type": fac,
                    "crowd_level": crd,
                    "realtime_crowd_level": round(realtime_crowd, 1) if realtime_crowd else None,
                    "notes": notes,
                    "toilet_name": toilet_name,
                    "platform_name": platform,
                    "message": msg,
                    "latitude": dest_lat,
                    "longitude": dest_lng,
                    "location_type": location_type,
                    "toilet_id": toilet_id
                })
            except Exception as e:
                traceback.print_exc()
                continue

        return results

    except Exception as e:
        traceback.print_exc()
        return []

@app.post("/report_congestion")
def report_congestion(report: CongestionReport):
    try:
        data = {
            "toilet_id": report.toilet_id,
            "congestion_level": report.congestion_level,
            "user_id": report.user_id if report.user_id else None
        }
        supabase.table("congestion_reports").insert(data).execute()
        return {"status": "success", "message": "Report received"}
    except Exception as e:
        print(f"Report Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save report")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)