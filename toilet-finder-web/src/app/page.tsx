'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Train, ArrowRight, MapPin, CheckCircle, Info, User, Map as MapIcon, Navigation } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- TrainRadar Component (Inline Implementation) ---
const TrainRadar = ({ userCar, targetCar, maxCars = 10 }: { userCar: number, targetCar: number, maxCars?: number }) => {
  const cars = Array.from({ length: maxCars }, (_, i) => i + 1);

  return (
    <div className="w-full bg-slate-200 rounded-full h-12 relative flex items-center px-2 overflow-hidden">
      {/* レール */}
      <div className="absolute top-1/2 left-0 w-full h-1 bg-slate-300 -translate-y-1/2" />
      
      <div className="flex justify-between w-full relative z-10">
        {cars.map((carNum) => {
          const isUser = carNum === userCar;
          const isTarget = Math.round(targetCar) === carNum;
          
          return (
            <div key={carNum} className="relative flex flex-col items-center justify-center w-full">
              {/* 車両の箱 */}
              <div className={`
                w-full h-3 mx-0.5 rounded-sm transition-colors
                ${isUser ? 'bg-blue-500' : isTarget ? 'bg-red-400' : 'bg-slate-400'}
              `} />
              
              {/* アイコン表示 */}
              <div className="absolute top-1/2 -translate-y-1/2 flex justify-center items-center">
                 {isUser && (
                   <motion.div 
                     initial={{ scale: 0 }} animate={{ scale: 1 }}
                     className="bg-blue-600 text-white p-1 rounded-full shadow-lg z-20"
                   >
                     <User size={12} fill="currentColor" />
                   </motion.div>
                 )}
                 {isTarget && !isUser && (
                   <motion.div 
                     initial={{ scale: 0 }} animate={{ scale: 1 }}
                     className="bg-red-500 text-white p-1 rounded-full shadow-lg z-10"
                   >
                     <div className="text-[8px] font-bold">WC</div>
                   </motion.div>
                 )}
              </div>
              
              {/* 番号 */}
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
  notes?: string;
  platform_name?: string;
  message: string;
  latitude?: number; 
  longitude?: number;
  location_type?: 'exact' | 'station'; // 位置情報のタイプ
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

  useEffect(() => {
    const fetchLines = async () => {
      setLoading(true);
      try {
        let url = `${API_BASE_URL}/lines`;
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              const { latitude, longitude } = position.coords;
              url += `?lat=${latitude}&lng=${longitude}`;
              await getLinesData(url);
            },
            async () => await getLinesData(url)
          );
        } else {
          await getLinesData(url);
        }
      } catch (e) {
        setErrorMsg("初期化エラー");
        setLoading(false);
      }
    };
    const getLinesData = async (url: string) => {
      try {
        const res = await fetch(url);
        if (res.ok) {
            const data = await res.json();
            setLines(data);
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    fetchLines();
  }, []);

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

      if (navigator.geolocation) {
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
    <main className="min-h-screen bg-gray-50 font-sans pb-10">
      <header className="bg-white p-4 shadow-sm sticky top-0 z-10">
        <div className="flex justify-between items-center max-w-md mx-auto">
          <h1 className="text-lg font-black text-gray-800 flex items-center gap-2">
            <AlertTriangle className="text-blue-600 w-5 h-5" />
            すぐそこトイレ <span className="text-xs font-normal text-gray-500">車内利用編</span>
          </h1>
          {step !== 'line' && (
            <button onClick={reset} className="text-xs text-gray-400 font-bold border px-2 py-1 rounded">最初に戻る</button>
          )}
        </div>
      </header>

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
                        
                        {pred.platform_name && pred.platform_name !== 'ホーム' && pred.platform_name !== 'nan' && (
                          <span className="inline-block bg-orange-100 text-orange-800 text-[10px] font-bold px-2 py-0.5 rounded mt-1">
                            {pred.platform_name} 到着
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="bg-blue-100 p-2 rounded-lg text-blue-700"><Train className="w-5 h-5" /></div>
                        <div>
                          <p className="text-xs text-gray-400 font-bold">トイレまでの距離</p>
                          {pred.target_car <= 0 ? (
                              <p className="text-sm font-bold text-gray-500">詳細データ収集中</p>
                          ) : (
                              <p className="text-sm font-bold text-gray-700">{pred.walking_cars < 0.5 ? '目の前' : `${pred.walking_cars}両分 歩く`} <span className="text-xs font-normal ml-1">({pred.facility_type})</span></p>
                          )}
                        </div>
                      </div>
                      
                      {/* メモ欄の強調表示 - AI生成テキスト等の受け皿 */}
                      {pred.notes && (
                        <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg my-3">
                           <p className="text-sm font-bold text-yellow-800 flex items-center gap-2 mb-1">
                             <Navigation size={16} /> 
                             ルート案内 / メモ
                           </p>
                           <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{pred.notes}</p>
                        </div>
                      )}

                      <p className={`text-sm font-bold text-center mt-2 text-gray-500`}>
                        {pred.target_car <= 0 ? 'トイレ情報はあります' : pred.message}
                      </p>
                      
                      {/* Google Map への誘導ボタン (条件分岐: 正確な位置のみ表示) */}
                      {pred.latitude && pred.longitude && pred.location_type === 'exact' && (
                        <a 
                          href={`https://www.google.com/maps/dir/?api=1&destination=${pred.latitude},${pred.longitude}&travelmode=walking`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-3 block w-full bg-blue-600 hover:bg-blue-700 text-white text-center font-bold py-3 rounded-lg flex items-center justify-center gap-2 shadow-md transition-colors"
                        >
                          <MapIcon size={18} />
                          ここへ行く (Google Map)
                        </a>
                      )}
                    </div>
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