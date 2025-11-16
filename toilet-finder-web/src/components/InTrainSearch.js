"use client";

import { useState, useEffect } from 'react';
// ★削除: Supabase関連

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
        throw new Error("トイレが見つかりませんでした");
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
    <div className="p-4 w-full">
      <div className="bg-white p-3 rounded-xl shadow-sm border border-gray-200">
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="form-control w-full">
              <label className="label py-0 pb-1"><span className="label-text text-xs font-bold text-gray-500">路線</span></label>
              <select className="select select-bordered select-sm w-full font-bold text-gray-700" value={line} onChange={(e) => setLine(e.target.value)}>
                {lineList.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div className="form-control w-full">
              <label className="label py-0 pb-1"><span className="label-text text-xs font-bold text-gray-500">駅</span></label>
              <select className="select select-bordered select-sm w-full font-bold text-gray-700" value={station} onChange={(e) => setStation(e.target.value)} disabled={!stationList.length}>
                {stationList.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {directionList.length > 0 ? (
              <div className="form-control w-full">
                <label className="label py-0 pb-1"><span className="label-text text-xs font-bold text-gray-500">方面</span></label>
                <select className="select select-bordered select-sm w-full font-bold text-gray-700" value={direction} onChange={(e) => setDirection(e.target.value)}>
                  {directionList.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            ) : <div className="hidden"></div>}
            <div className="form-control w-full">
              <label className="label py-0 pb-1"><span className="label-text text-xs font-bold text-gray-500">乗車位置</span></label>
              <select className="select select-bordered select-sm w-full font-bold text-gray-700" value={car} onChange={(e) => setCar(e.target.value)}>
                {[...Array(15)].map((_, i) => (<option key={i + 1} value={i + 1}>{i + 1}号車</option>))}
              </select>
            </div>
          </div>
        </div>
        <button className="btn bg-blue-600 hover:bg-blue-700 text-white border-none btn-sm w-full font-bold mt-4 shadow-sm" onClick={handleSearch} disabled={isLoading || !line || !station}>
          {isLoading ? <span className="loading loading-spinner loading-xs"></span> : "トイレを探す"}
        </button>
      </div>
      {error && <div className="alert alert-error mt-4 text-sm py-2 rounded-lg text-white"><span>{error}</span></div>}
      {result && (
        <div className="mt-4 animate-fade-in">
          <div className="text-xs text-gray-500 font-bold mb-2 ml-1">▼ あなたに最適なトイレ</div>
          <div className="bg-white rounded-lg shadow-md border border-gray-200 p-4">
              <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2 mb-1">
                {result.is_station_toilet && "🚉"} {result.name}
              </h2>
              <p className="text-xs text-gray-600 mb-3">{result.address}</p>
              <div className="flex gap-2 mb-3">
                {result.is_wheelchair_accessible && <span className="badge badge-sm badge-outline text-blue-600 border-blue-600">♿ 車椅子</span>}
                {result.has_diaper_changing_station && <span className="badge badge-sm badge-outline text-pink-600 border-pink-600">👶 おむつ</span>}
                {result.is_ostomate_accessible && <span className="badge badge-sm badge-outline text-green-600 border-green-600">✚ オストメイト</span>}
              </div>
              <a href={`http://googleusercontent.com/maps.google.com/maps?q=${result.latitude},${result.longitude}`} target="_blank" rel="noopener noreferrer" className="btn bg-blue-600 hover:bg-blue-700 text-white border-none btn-sm w-full no-underline">
                ルート案内
              </a>
          </div>
        </div>
      )}
    </div>
  );
}