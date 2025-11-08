"use client";

import { useState, useEffect } from 'react';

export default function InTrainSearch() {
  const [station, setStation] = useState(''); 
  const [line, setLine] = useState('');       
  const [car, setCar] = useState('5');
  const [stationList, setStationList] = useState([]);
  const [lineList, setLineList] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStationLoading, setIsStationLoading] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchLines = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/lines`);
        if (!res.ok) throw new Error(`路線リスト取得エラー: ${res.status}`);
        const data = await res.json();
        setLineList(data);
        if (data.length > 0) setLine(data[0]);
      } catch (err) {
        console.error("路線リストの取得に失敗", err);
        setError("路線リストのAPI取得に失敗しました");
      }
    };
    fetchLines();
  }, []);

  useEffect(() => {
    if (!line) {
        setStationList([]);
        setStation('');
        return;
    }

    const fetchStationsByLine = async () => {
      try {
        setIsStationLoading(true);
        const res = await fetch(`${API_BASE_URL}/api/stations-by-line?line=${encodeURIComponent(line)}`);
        if (!res.ok) throw new Error(`駅リスト取得エラー: ${res.status}`);
        const data = await res.json();
        setStationList(data);
        if (data.length > 0) setStation(data[0]); else setStation('');
      } catch (err) {
        console.error("駅リストの取得に失敗", err);
        setError("駅リストのAPI取得に失敗しました");
      } finally {
        setIsStationLoading(false);
      }
    };
    fetchStationsByLine();
  }, [line]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!line || !station) {
        setError("路線と駅を選択してください。");
        return;
    }
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/train-toilet?station=${encodeURIComponent(station)}&line=${encodeURIComponent(line)}&car=${car}`);
      if (!res.ok) {
        if (res.status === 404) throw new Error("この場所から最適なトイレの情報がまだ登録されていません。");
        throw new Error(`サーバーエラー: ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error("乗車中検索エラー:", err);
      setError(err.message || "検索中にエラーが発生しました。");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-5 rounded-xl shadow-sm border border-blue-100">
      <h2 className="text-lg font-bold mb-4 text-blue-800 flex items-center gap-2">
        <span className="text-2xl">🚃</span> 乗車中から検索
      </h2>
      
      <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-4 max-w-3xl">
        <div className="form-control w-full sm:w-48">
          <label className="label-text font-bold text-gray-600 mb-1 ml-1">路線</label>
          <select className="select select-bordered w-full" value={line} onChange={(e) => setLine(e.target.value)} disabled={lineList.length === 0}>
            {lineList.length === 0 && <option>読み込み中...</option>}
            {lineList.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div className="form-control w-full sm:w-48">
          <label className="label-text font-bold text-gray-600 mb-1 ml-1">駅</label>
          <select className="select select-bordered w-full" value={station} onChange={(e) => setStation(e.target.value)} disabled={isStationLoading || stationList.length === 0}>
            {isStationLoading ? <option>駅を読込中...</option> : stationList.length === 0 ? <option>駅なし</option> : stationList.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="form-control w-24">
          <label className="label-text font-bold text-gray-600 mb-1 ml-1">号車</label>
          <div className="join">
            <input type="number" value={car} min="1" max="15" onChange={(e) => setCar(e.target.value)} className="input input-bordered join-item w-full text-center" required />
            <span className="btn btn-disabled join-item bg-base-200 border-base-300 text-gray-500 px-2">号車</span>
          </div>
        </div>
        <button type="submit" className="btn btn-primary px-8" disabled={isLoading || !line || !station}>
          {isLoading ? <span className="loading loading-spinner"></span> : '検索'}
        </button>
      </form>

      {error && (
        <div className="mt-5 p-3 bg-red-50 text-red-700 text-sm font-bold rounded-lg border border-red-200 flex items-center gap-3">
          <span className="text-xl">🚨</span><span>{error}</span>
        </div>
      )}

      {result && (
        <div className="mt-6 p-5 bg-blue-50 border-l-4 border-blue-500 rounded-r-xl animation-fade-in shadow-sm">
          <h3 className="font-bold text-blue-800 mb-2 flex items-center gap-2 text-lg">
            <span>🎯</span> このドアから一番便利なトイレ
          </h3>
          <div className="text-xl font-extrabold text-gray-900 ml-1">{result.name}</div>
          <p className="text-sm text-gray-600 mt-1 ml-1 flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>
            {result.address}
          </p>
           <div className="mt-4 flex gap-2 flex-wrap">
              <span className={`badge ${result.is_wheelchair_accessible ? "badge-success text-white" : "badge-ghost text-gray-400"} gap-1 pl-1.5`}>♿ 車椅子</span>
              <span className={`badge ${result.has_diaper_changing_station ? "badge-success text-white" : "badge-ghost text-gray-400"} gap-1 pl-1.5`}>👶 おむつ</span>
              <span className={`badge ${result.is_ostomate_accessible ? "badge-success text-white" : "badge-ghost text-gray-400"} gap-1 pl-1.5`}>✚ オストメイト</span>
           </div>
           
           {/* ★修正: ルート案内ボタン (ラベル付き・公式URL) */}
           <a 
            href={`https://www.google.com/maps/dir/?api=1&destination=${result.latitude},${result.longitude}`}
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn btn-primary w-full sm:w-auto mt-5 text-white no-underline flex items-center justify-center gap-2 px-6"
          >
            <span className="text-xl">🗺️</span>
            <span className="font-bold">ルート案内</span>
          </a>
        </div>
      )}
    </div>
  );
}