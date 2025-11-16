"use client";

import { useState, useEffect } from 'react';

export default function InTrainSearch() {
  const [line, setLine] = useState('');       
  const [station, setStation] = useState(''); 
  const [direction, setDirection] = useState(''); 
  const [car, setCar] = useState('5'); 

  const [lineList, setLineList] = useState([]);
  const [stationList, setStationList] = useState([]);
  const [directionList, setDirectionList] = useState([]);

  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // 1. 路線リスト取得
  useEffect(() => {
    const fetchLines = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/train/lines`);
        if (!res.ok) return;
        const data = await res.json();
        setLineList(data);
        if (data.length > 0) setLine(data[0]);
      } catch (e) { console.error(e); }
    };
    fetchLines();
  }, [API_BASE_URL]);

  // 2. 駅リスト取得
  useEffect(() => {
    if (!line) return;
    const fetchStations = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/train/stations?line=${encodeURIComponent(line)}`);
        if (!res.ok) return;
        const data = await res.json();
        setStationList(data);
        if (data.length > 0) setStation(data[0]);
        else setStation('');
      } catch (e) { console.error(e); }
    };
    fetchStations();
  }, [line, API_BASE_URL]);

  // 3. 方面リスト取得
  useEffect(() => {
    if (!line || !station) {
      setDirectionList([]);
      setDirection('');
      return;
    }
    const fetchDirections = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/train/directions?line=${encodeURIComponent(line)}&station=${encodeURIComponent(station)}`);
        if (!res.ok) return;
        const data = await res.json();
        setDirectionList(data);
        if (data.length > 0) setDirection(data[0]);
        else setDirection('');
      } catch (e) { console.error(e); }
    };
    fetchDirections();
  }, [line, station, API_BASE_URL]);

  // 4. 検索実行
  const handleSearch = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const params = new URLSearchParams({
        line,
        station,
        car: car.toString(),
      });
      if (direction) params.append("direction", direction);

      const res = await fetch(`${API_BASE_URL}/api/train/search?${params.toString()}`);
      
      if (!res.ok) {
        throw new Error("該当するトイレが見つかりませんでした");
      }
      
      const data = await res.json();
      setResult(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-lg mx-auto">
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
        
        {/* 横並びレイアウト */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          
          {/* 路線 */}
          <div className="flex flex-col">
            <label className="text-xs font-bold text-gray-500 mb-1">路線</label>
            <select className="select select-bordered select-sm w-full" value={line} onChange={(e) => setLine(e.target.value)}>
              {lineList.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>

          {/* 駅 */}
          <div className="flex flex-col">
            <label className="text-xs font-bold text-gray-500 mb-1">駅</label>
            <select className="select select-bordered select-sm w-full" value={station} onChange={(e) => setStation(e.target.value)} disabled={!stationList.length}>
              {stationList.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          {/* 方面 (あれば表示) */}
          {directionList.length > 0 && (
             <div className="flex flex-col">
               <label className="text-xs font-bold text-gray-500 mb-1">方面</label>
               <select className="select select-bordered select-sm w-full" value={direction} onChange={(e) => setDirection(e.target.value)}>
                 {directionList.map((d) => <option key={d} value={d}>{d}</option>)}
               </select>
             </div>
          )}

          {/* 号車 */}
          <div className="flex flex-col">
            <label className="text-xs font-bold text-gray-500 mb-1">乗車位置</label>
            <select className="select select-bordered select-sm w-full" value={car} onChange={(e) => setCar(e.target.value)}>
              {[...Array(15)].map((_, i) => <option key={i + 1} value={i + 1}>{i + 1}号車</option>)}
            </select>
          </div>
        </div>

        {/* ボタン (青色強制) */}
        <button 
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md transition-colors"
          onClick={handleSearch}
          disabled={isLoading || !line || !station}
        >
          {isLoading ? "検索中..." : "トイレを探す"}
        </button>
      </div>

      {/* エラー */}
      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 text-sm rounded-lg">
          {error}
        </div>
      )}

      {/* 結果カード */}
      {result && (
        <div className="mt-6 bg-white rounded-xl shadow-md border border-blue-100 overflow-hidden animate-fade-in">
          <div className="bg-blue-50 p-3 border-b border-blue-100">
            <div className="text-xs text-blue-800 font-bold">▼ 最適なトイレ</div>
          </div>
          <div className="p-4">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                {result.is_station_toilet && "🚉"} {result.name}
              </h2>
              <p className="text-sm text-gray-600 mb-4">{result.address}</p>
              
              <div className="flex gap-2 mb-4">
                {result.is_wheelchair_accessible && <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">♿ 車椅子</span>}
                {result.has_diaper_changing_station && <span className="px-2 py-1 text-xs bg-pink-100 text-pink-800 rounded">👶 おむつ</span>}
                {result.is_ostomate_accessible && <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">✚ オストメイト</span>}
              </div>

              <a 
                href={`https://www.google.com/maps/dir/?api=1&destination=${result.latitude},${result.longitude}`}
                target="_blank" 
                rel="noopener noreferrer" 
                className="block w-full text-center py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors"
              >
                ルート案内
              </a>
          </div>
        </div>
      )}
    </div>
  );
}