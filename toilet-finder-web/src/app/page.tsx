'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Train, ArrowRight, MapPin, CheckCircle, Info, User, Navigation, LogIn, Crown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
// -----------------------------------------------------------------------------
// 本番用コード (Vercelデプロイ用)
// -----------------------------------------------------------------------------
import { createClient } from '@supabase/supabase-js';

// 環境変数の取得
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// ★修正: URLとKeyが存在する場合のみクライアントを作成
// 環境変数がロードされていない場合やビルド時でもクラッシュしないようにnullを許容します
const supabase = (supabaseUrl && supabaseKey) 
  ? createClient(supabaseUrl, supabaseKey) 
  : null;


// --- TrainRadar Component (Inline) ---
const TrainRadar = ({ userCar, targetCar, maxCars = 10 }: { userCar: number, targetCar: number, maxCars?: number }) => {
  const cars = Array.from({ length: maxCars }, (_, i) => i + 1);

  return (
    <div className="w-full bg-slate-200 rounded-full h-12 relative flex items-center px-2 overflow-hidden">
      <div className="absolute top-1/2 left-0 w-full h-1 bg-slate-300 -translate-y-1/2" />
      <div className="flex justify-between w-full relative z-10">
        {cars.map((carNum) => {
          const isUser = carNum === userCar;
          const isTarget = Math.round(targetCar) === carNum;
          
          return (
            <div key={carNum} className="relative flex flex-col items-center justify-center w-full">
              <div className={`
                w-full h-3 mx-0.5 rounded-sm transition-colors
                ${isUser ? 'bg-blue-500' : isTarget ? 'bg-red-400' : 'bg-slate-400'}
              `} />
              <div className="absolute top-1/2 -translate-y-1/2 flex justify-center items-center">
                 {isUser && (
                   <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="bg-blue-600 text-white p-1 rounded-full shadow-lg z-20">
                     <User size={12} fill="currentColor" />
                   </motion.div>
                 )}
                 {isTarget && !isUser && (
                   <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="bg-red-500 text-white p-1 rounded-full shadow-lg z-10">
                     <div className="text-[8px] font-bold">WC</div>
                   </motion.div>
                 )}
              </div>
              <span className="text-[8px] text-slate-500 mt-4 absolute top-2">{carNum}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// --- 型定義 ---
type Line = {
  id: string;
  name: string;
  color: string;
  direction_1_name: string;
  direction_minus_1_name: string;
  max_cars: number;
};

type Station = {
  id: string;
  name: string;
  order: number;
  lat?: number;
  lng?: number;
  dir_1_label?: string;
  dir_m1_label?: string;
};

type PredictionResult = {
  station_id: string;
  station_name: string;
  stop_order: number;
  walking_cars: number;
  target_car: number;
  facility_type: string;
  crowd_level: number;
  realtime_crowd_level?: number;
  notes?: string;
  toilet_name?: string;
  platform_name?: string;
  message: string;
  latitude?: number; 
  longitude?: number;
  location_type?: 'exact' | 'station';
  toilet_id?: string;
};

// クライアントサイドでの環境変数参照
const API_BASE_URL = (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) || 'http://localhost:8000';

export default function Home() {
  const [step, setStep] = useState<'line' | 'direction' | 'car' | 'result'>('line');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [lines, setLines] = useState<Line[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  
  const [selectedLine, setSelectedLine] = useState<Line | null>(null);
  const [direction, setDirection] = useState<number>(1); 
  const [currentStation, setCurrentStation] = useState<Station | null>(null);
  const [selectedCar, setSelectedCar] = useState<number | null>(null);
  
  const [predictions, setPredictions] = useState<PredictionResult[]>([]);
  
  // Auth State
  const [user, setUser] = useState<any>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isPremium, setIsPremium] = useState(false);

  // 1. Auth Initialization
  useEffect(() => {
    // ★修正: supabaseクライアントが存在しない場合は処理をスキップ
    if (!supabase) {
      console.warn("Supabase client is not initialized. Check your environment variables.");
      return;
    }

    const checkSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      if (session?.user) {
        const { data } = await supabase.from('profiles').select('is_premium').eq('id', session.user.id).single();
        setIsPremium(data?.is_premium || false);
      }
    };
    checkSession();

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => authListener.subscription.unsubscribe();
  }, []);

  // 2. Fetch Lines (with Geolocation)
  useEffect(() => {
    const fetchLines = async () => {
      setLoading(true);
      try {
        let url = `${API_BASE_URL}/lines`;
        
        if (typeof navigator !== 'undefined' && navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              const { latitude, longitude } = position.coords;
              url += `?lat=${latitude}&lng=${longitude}`;
              await getLinesData(url);
            },
            async (error) => {
              console.warn("Geolocation failed or denied:", error);
              await getLinesData(url);
            }
          );
        } else {
          await getLinesData(url);
        }
      } catch (e) {
        console.error(e);
        setErrorMsg("路線の取得に失敗しました");
        setLoading(false);
      }
    };

    const getLinesData = async (url: string) => {
      try {
        const res = await fetch(url).catch(err => {
            console.warn("API fetch failed:", err);
            return null;
        });
        
        if (res && res.ok) {
            const data = await res.json();
            setLines(data);
        } else {
            console.error("Failed to fetch lines");
            setErrorMsg("データの取得に失敗しました");
        }
      } catch (e) { 
          console.error(e);
          setErrorMsg("API接続エラー");
      }
      setLoading(false);
    };

    fetchLines();
  }, []);

  const handleAuth = async (isSignUp: boolean) => {
    // ★修正: クライアントチェックを追加
    if (!supabase) {
      alert("認証機能は現在利用できません (環境設定を確認してください)");
      return;
    }
    
    try {
      let result;
      if (isSignUp) {
        result = await supabase.auth.signUp({ email, password });
      } else {
        result = await supabase.auth.signInWithPassword({ email, password });
      }
      if (result.error) throw result.error;
      setAuthModalOpen(false);
      
      if (isSignUp && result.data.user) {
        await supabase.from('profiles').insert({ id: result.data.user.id, is_premium: false });
      }
      alert(isSignUp ? "登録しました" : "ログインしました");
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleUpgrade = async () => {
    if (!user || !supabase) return;
    const confirm = window.confirm("月額300円でプレミアム会員になりますか？");
    if (confirm) {
      await supabase.from('profiles').update({ is_premium: true }).eq('id', user.id);
      setIsPremium(true);
      alert("プレミアム会員になりました！");
    }
  };

  const handleReport = async (toiletId: string, level: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/report_congestion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          toilet_id: toiletId,
          congestion_level: level,
          user_id: user?.id
        })
      });
      if (!res.ok) throw new Error("Failed");
      alert("投稿ありがとうございます！");
    } catch (e) {
      console.error(e);
      alert("送信に失敗しました");
    }
  };

  const handleLineSelect = async (line: Line) => {
    setLoading(true);
    setSelectedLine(line);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_BASE_URL}/stations?line_id=${line.id}`);
      if (!res.ok) throw new Error('API Error');
      const stationData: Station[] = await res.json();

      if (!Array.isArray(stationData)) {
          throw new Error("Invalid Data");
      }

      setStations(stationData);

      if (typeof navigator !== 'undefined' && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const { latitude, longitude } = position.coords;
            let nearest: Station | null = null;
            let minDist = Infinity;

            stationData.forEach(st => {
              const sLat = st.lat || 0;
              const sLng = st.lng || 0;
              if (sLat !== 0 && sLng !== 0) {
                const d = Math.sqrt(Math.pow(sLat - latitude, 2) + Math.pow(sLng - longitude, 2));
                if (d < minDist) {
                  minDist = d;
                  nearest = st;
                }
              }
            });

            if (nearest) {
              setCurrentStation(nearest);
            } else {
              setCurrentStation(stationData[0]);
            }
            setLoading(false);
            setStep('direction');
          },
          () => {
            setCurrentStation(stationData[0]);
            setLoading(false);
            setStep('direction');
          }
        );
      } else {
        setCurrentStation(stationData[0]);
        setLoading(false);
        setStep('direction');
      }
    } catch (e) {
      console.error(e);
      setErrorMsg("駅データの取得に失敗しました");
      setLoading(false);
    }
  };

  const handleDirectionSelect = (dir: number) => {
    setDirection(dir);
    setStep('car');
  };

  const handleCarSelect = async (car: number) => {
    setSelectedCar(car);
    setLoading(true);
    try {
      const url = `${API_BASE_URL}/predict?line_id=${selectedLine?.id}&current_station_id=${currentStation?.id}&user_car=${car}&direction=${direction}`;
      const res = await fetch(url);
      const results = await res.json();
      if (!Array.isArray(results) || results.length === 0) {
        setErrorMsg("データが見つかりませんでした。別の駅か号車を試してください。");
        setLoading(false);
        return;
      }
      setPredictions(results);
      setStep('result');
      setLoading(false);
    } catch (e) {
      console.error("Prediction Error:", e);
      setErrorMsg("予測データの取得に失敗しました。サーバーエラーの可能性があります。");
      setLoading(false);
    }
  };

  const reset = () => {
    setStep('line');
    setSelectedLine(null);
    setPredictions([]);
    setErrorMsg(null);
  };

  const getDirLabel = (dir: number) => {
    if (!selectedLine) return "";
    if (currentStation) {
      if (dir === 1 && currentStation.dir_1_label) return currentStation.dir_1_label;
      if (dir === -1 && currentStation.dir_m1_label) return currentStation.dir_m1_label;
    }
    return dir === 1 ? selectedLine.direction_1_name : selectedLine.direction_minus_1_name;
  };

  const maxCars = selectedLine?.max_cars || 10;
  const carButtons = Array.from({ length: maxCars }, (_, i) => i + 1);

  return (
    <main className="min-h-screen bg-gray-50 font-sans pb-10 relative">
      <header className="bg-white p-4 shadow-sm sticky top-0 z-10">
        <div className="flex justify-between items-center max-w-md mx-auto">
          <h1 className="text-lg font-black text-gray-800 flex items-center gap-2">
            <AlertTriangle className="text-blue-600 w-5 h-5" />
            すぐそこトイレ
          </h1>
          <div className="flex gap-2">
            {!user ? (
              <button onClick={() => setAuthModalOpen(true)} className="text-xs bg-slate-800 text-white px-3 py-1 rounded-full font-bold flex items-center gap-1">
                <LogIn size={12} /> ログイン
              </button>
            ) : (
              <div className="flex items-center gap-2">
                {isPremium && <Crown size={16} className="text-yellow-500 fill-yellow-500" />}
                <span className="text-xs font-bold text-slate-600 truncate max-w-[80px]">{user.email}</span>
              </div>
            )}
            {step !== 'line' && (
              <button onClick={reset} className="text-xs text-gray-400 font-bold border px-2 py-1 rounded">戻る</button>
            )}
          </div>
        </div>
      </header>

      {/* Auth Modal */}
      {authModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm">
            <h2 className="text-xl font-bold mb-4 text-center">ログイン / 登録</h2>
            <input type="email" placeholder="メールアドレス" className="w-full p-3 border rounded-lg mb-3" value={email} onChange={e => setEmail(e.target.value)} />
            <input type="password" placeholder="パスワード" className="w-full p-3 border rounded-lg mb-4" value={password} onChange={e => setPassword(e.target.value)} />
            <div className="flex gap-2 mb-4">
              <button onClick={() => handleAuth(false)} className="flex-1 bg-blue-600 text-white py-2 rounded-lg font-bold">ログイン</button>
              <button onClick={() => handleAuth(true)} className="flex-1 bg-slate-200 text-slate-700 py-2 rounded-lg font-bold">新規登録</button>
            </div>
            <button onClick={() => setAuthModalOpen(false)} className="w-full text-sm text-slate-400">閉じる</button>
          </div>
        </div>
      )}

      {/* Premium Banner (for free users) */}
      {user && !isPremium && (
        <div className="bg-gradient-to-r from-yellow-100 to-orange-100 p-2 text-center text-xs font-bold text-orange-800 cursor-pointer" onClick={handleUpgrade}>
          👑 プレミアムプランで広告非表示＆詳細機能を利用 (タップで登録)
        </div>
      )}

      <div className="max-w-md mx-auto px-4 pt-6">
        {errorMsg && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-4 text-sm font-bold flex items-center gap-2">
            <AlertTriangle size={16} />
            {errorMsg}
          </div>
        )}

        <AnimatePresence mode="wait">
          {step === 'line' && (
            <motion.div key="line" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
              <div className="text-center space-y-2">
                <p className="text-sm font-bold text-gray-500">STEP 1</p>
                <h2 className="text-2xl font-black text-gray-800">{loading ? "現在地を特定中..." : "乗っている路線は？"}</h2>
              </div>
              {loading ? <div className="text-center py-10 text-gray-400">Loading...</div> : (
                <div className="grid gap-3">
                  {lines.map((line) => (
                    <button key={line.id} onClick={() => handleLineSelect(line)} className="p-6 rounded-2xl shadow-lg text-left bg-white border-l-8" style={{ borderLeftColor: line.color }}>
                      <span className="text-xl font-bold">{line.name}</span>
                      <ArrowRight className="text-gray-300 float-right" />
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {step === 'direction' && (
            <motion.div key="direction" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
              <div className="bg-blue-50 p-3 rounded-lg text-center mb-4">
                <p className="text-xs text-blue-600 font-bold">現在地</p>
                <p className="text-lg font-black text-blue-800 flex items-center justify-center gap-2">
                  <MapPin className="w-5 h-5" /> {currentStation?.name} 駅
                </p>
              </div>
              <div className="text-center space-y-2">
                <p className="text-sm font-bold text-gray-500">STEP 2</p>
                <h2 className="text-2xl font-black text-gray-800">進行方向は？</h2>
              </div>
              <div className="grid gap-4">
                <button onClick={() => handleDirectionSelect(1)} className="bg-white p-6 rounded-2xl shadow-lg flex justify-between items-center border-2 border-transparent hover:border-blue-500">
                  <div className="flex flex-col text-left">
                    <span className="text-2xl font-black text-gray-800">{getDirLabel(1)}</span>
                    <span className="text-xs text-gray-400 font-bold mt-1">方面</span>
                  </div>
                  <ArrowRight className="w-8 h-8 text-blue-600" />
                </button>
                <button onClick={() => handleDirectionSelect(-1)} className="bg-white p-6 rounded-2xl shadow-lg flex justify-between items-center border-2 border-transparent hover:border-orange-500">
                  <div className="flex flex-col text-left">
                    <span className="text-2xl font-black text-gray-800">{getDirLabel(-1)}</span>
                    <span className="text-xs text-gray-400 font-bold mt-1">方面</span>
                  </div>
                  <ArrowRight className="w-8 h-8 text-orange-600" />
                </button>
              </div>
            </motion.div>
          )}

          {step === 'car' && (
            <motion.div key="car" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-6">
              <div className="text-center space-y-2">
                <p className="text-sm font-bold text-gray-500">STEP 3</p>
                <h2 className="text-2xl font-black text-gray-800">何号車にいますか？</h2>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {carButtons.map((num) => (
                  <button key={num} onClick={() => handleCarSelect(num)} className="aspect-square bg-white rounded-xl shadow-md text-2xl font-black text-gray-700 hover:border-blue-500 border-2 border-transparent">
                    {num}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {step === 'result' && (
            <motion.div key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <h2 className="text-center text-xl font-bold text-gray-800 mb-6">ルート判定結果</h2>
              <div className="space-y-4">
                {predictions.map((pred) => (
                  <div key={pred.station_id} className={`relative p-5 rounded-2xl border-2 bg-white border-gray-100 shadow-lg`}>
                    <div className="mb-4">
                        {pred.target_car > 0 ? (
                             <TrainRadar 
                               userCar={selectedCar || 1} 
                               targetCar={pred.target_car} 
                               maxCars={maxCars}
                             />
                        ) : (
                            <div className="bg-gray-100 border border-gray-300 h-10 rounded-lg flex items-center justify-center gap-2 text-xs text-gray-500 font-bold">
                                <Info className="w-4 h-4 text-blue-500" />
                                <span>詳細な号車情報は現在収集中です</span>
                            </div>
                        )}
                    </div>
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="text-xs font-bold text-gray-500">{pred.stop_order === 0 ? '当駅 (現在地)' : Math.abs(pred.stop_order) === 1 ? '次の駅' : 'その次の駅'}</p>
                        <h3 className="text-2xl font-black text-gray-800">{pred.station_name}</h3>
                        
                        {/* トイレ名を表示 */}
                        {pred.toilet_name && (
                          <p className="text-sm font-bold text-slate-700 mt-1">{pred.toilet_name}</p>
                        )}

                        {pred.platform_name && pred.platform_name !== 'ホーム' && pred.platform_name !== 'nan' && (
                          <span className="inline-block bg-orange-100 text-orange-800 text-[10px] font-bold px-2 py-0.5 rounded mt-1">
                            {pred.platform_name} 到着
                          </span>
                        )}
                        {/* リアルタイム混雑表示 */}
                        {pred.realtime_crowd_level && (
                          <div className={`mt-1 text-xs font-bold ${pred.realtime_crowd_level < 1.5 ? 'text-blue-600' : pred.realtime_crowd_level > 2.5 ? 'text-red-600' : 'text-green-600'}`}>
                            現在: {pred.realtime_crowd_level < 1.5 ? '空いてるかも' : pred.realtime_crowd_level > 2.5 ? '激混み注意' : '普通'}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* メモ欄 */}
                    {pred.notes && (
                      <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg my-3">
                          <p className="text-sm font-bold text-yellow-800 flex items-center gap-2 mb-1">
                            <Navigation size={16} /> 
                            ルート案内 / メモ
                          </p>
                          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{pred.notes}</p>
                      </div>
                    )}

                    {/* 投稿ボタン (トイレIDがある場合のみ) */}
                    {pred.toilet_id && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <p className="text-[10px] text-gray-400 font-bold text-center mb-2">混雑状況をシェア</p>
                        <div className="flex gap-2 justify-center">
                          <button onClick={() => handleReport(pred.toilet_id!, 1)} className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs font-bold border border-blue-100 hover:bg-blue-100">空き</button>
                          <button onClick={() => handleReport(pred.toilet_id!, 2)} className="px-3 py-1 bg-green-50 text-green-600 rounded-full text-xs font-bold border border-green-100 hover:bg-green-100">普通</button>
                          <button onClick={() => handleReport(pred.toilet_id!, 3)} className="px-3 py-1 bg-red-50 text-red-600 rounded-full text-xs font-bold border border-red-100 hover:bg-red-100">激混</button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}