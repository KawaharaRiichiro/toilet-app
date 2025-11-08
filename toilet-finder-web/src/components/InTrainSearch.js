"use client";

import { useState, useEffect } from 'react';

// 距離を整形するヘルパー関数
const formatDistance = (meters) => {
  if (typeof meters !== 'number' || isNaN(meters)) return '';
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
};

export default function InTrainSearch() {
  const [station, setStation] = useState(''); 
  const [line, setLine] = useState('');       
  const [car, setCar] = useState('5');
  const [stationList, setStationList] = useState([]);
  const [lineList, setLineList] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLineLoading, setIsLineLoading] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/stations`);
        if (!res.ok) throw new Error(`駅リスト取得エラー: ${res.status}`);
        const data = await res.json();
        setStationList(data);
        if (data.length > 0) setStation(data[0]);
      } catch (err) {
        console.error("駅リストの取得に失敗", err);
        setError("駅リストのAPI取得に失敗しました");
      }
    };
    fetchStations();
  }, []);

  useEffect(() => {
    if (!station) return;
    const fetchLines = async () => {
      try {
        setIsLineLoading(true);
        const res = await fetch(`${API_BASE_URL}/api/lines?station=${station}`);
        if (!res.ok) throw new Error(`路線リスト取得エラー: ${res.status}`);
        const data = await res.json();
        setLineList(data);
        if (data.length > 0) {
            setLine(data[0]);
        } else {
            setLine('');
        }
      } catch (err) {
        console.error("路線リストの取得に失敗", err);
        setError("路線リストのAPI取得に失敗しました");
      } finally {
        setIsLineLoading(false);
      }
    };
    fetchLines();
  }, [station]);

  const handleSearch = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/train-toilet?station=${station}&line=${line}&car=${car}`);
      if (!res.ok) {
        if (res.status === 404) {
            throw new Error("指定された条件（駅・路線・号車）に一致するドア情報が見つかりませんでした。");
        }
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
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h2 className="text-lg font-bold mb-3 text-gray-700">🚃 乗車中から検索</h2>
      
      <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-2">
        <div className="form-control w-full max-w-[120px]">
          <label className="label-text">駅</label>
          <select 
            className="select select-bordered select-sm"
            value={station}
            onChange={(e) => setStation(e.target.value)}
            disabled={stationList.length === 0}
          >
            {stationList.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="form-control w-full max-w-[120px]">
          <label className="label-text">路線</label>
          <select 
            className="select select-bordered select-sm"
            value={line}
            onChange={(e) => setLine(e.target.value)}
            disabled={isLineLoading || lineList.length === 0}
          >
            {isLineLoading ? (
              <option>読み込み中...</option>
            ) : (
              lineList.map(l => <option key={l} value={l}>{l}</option>)
            )}
          </select>
        </div>

        <div className="form-control">
          <label className="label-text">号車</label>
          <input 
            type="number" 
            value={car}
            min="1"
            max="15"
            onChange={(e) => setCar(e.target.value)}
            className="input input-bordered input-sm w-20" 
            required 
          />
        </div>

        <button type="submit" className="btn btn-primary btn-sm" disabled={isLoading}>
          {isLoading ? '検索中...' : '検索'}
        </button>
      </form>

      {error && (
        <div className="mt-3 text-red-600 text-sm font-bold">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-3 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
          <h3 className="font-bold text-blue-700 mb-1">🎯 ドアから一番近いトイレ</h3>
          <div className="text-base font-extrabold">
             {result.name}
             <span className="ml-2 text-red-500">({formatDistance(result.distance_meters)})</span>
          </div>
          <p className="text-sm text-gray-600">{result.address}</p>
           <div className="mt-2 flex gap-2 text-xs flex-wrap">
              <span className={result.is_wheelchair_accessible ? "badge badge-success text-white" : "badge badge-ghost"}>
                  車椅子{result.is_wheelchair_accessible ? '○' : '×'}
              </span>
              <span className={result.has_diaper_changing_station ? "badge badge-success text-white" : "badge badge-ghost"}>
                  おむつ{result.has_diaper_changing_station ? '○' : '×'}
              </span>
              <span className={result.is_ostomate_accessible ? "badge badge-success text-white" : "badge badge-ghost"}>
                  オストメイト{result.is_ostomate_accessible ? '○' : '×'}
              </span>
           </div>
           
           {/* ★新規追加: Googleマップでルート案内ボタン */}
           <a 
            href={`https://www.google.com/maps/dir/?api=1&destination=${result.latitude},${result.longitude}`}
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn btn-primary btn-sm w-full mt-3 text-white no-underline"
          >
            Googleマップでルート案内 🏃‍♂️
          </a>
        </div>
      )}
    </div>
  );
}