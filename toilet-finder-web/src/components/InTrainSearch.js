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
  // フォーム入力の状態
  const [line, setLine] = useState('');       // 路線を先に選択
  const [station, setStation] = useState(''); // 次に駅を選択
  const [car, setCar] = useState('5');
  
  // ドロップダウン用リストの状態
  const [lineList, setLineList] = useState([]);
  const [stationList, setStationList] = useState([]);
  
  // APIの結果
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStationLoading, setIsStationLoading] = useState(false); // 駅リスト読み込み中フラグ

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // 1. コンポーネント読み込み時に「全路線リスト」を取得
  useEffect(() => {
    const fetchLines = async () => {
      try {
        // ★修正: 全路線を取得するエンドポイントへ変更
        const res = await fetch(`${API_BASE_URL}/api/lines`);
        if (!res.ok) throw new Error(`路線リスト取得エラー: ${res.status}`);
        const data = await res.json();
        setLineList(data);
        // 初期値として最初の路線をセット
        if (data.length > 0) setLine(data[0]);
      } catch (err) {
        console.error("路線リストの取得に失敗", err);
        setError("路線リストのAPI取得に失敗しました");
      }
    };
    fetchLines();
  }, []);

  // 2. 路線が選択されたら「駅リスト」を取得
  useEffect(() => {
    if (!line) {
        setStationList([]);
        setStation('');
        return;
    }

    const fetchStationsByLine = async () => {
      try {
        setIsStationLoading(true);
        // ★修正: 路線名で駅を絞り込むエンドポイントへ変更
        const res = await fetch(`${API_BASE_URL}/api/stations-by-line?line=${encodeURIComponent(line)}`);
        if (!res.ok) throw new Error(`駅リスト取得エラー: ${res.status}`);
        const data = await res.json();
        setStationList(data);
        // 駅が変更されたら、選択中の駅をリセットまたは先頭にセット
        if (data.length > 0) {
            setStation(data[0]);
        } else {
            setStation('');
        }
      } catch (err) {
        console.error("駅リストの取得に失敗", err);
        setError("駅リストのAPI取得に失敗しました");
      } finally {
        setIsStationLoading(false);
      }
    };
    fetchStationsByLine();
  }, [line]); // lineが変更されるたびに実行

  // 検索実行時の処理
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
        if (res.status === 404) {
            throw new Error("指定された条件（路線・駅・号車）に一致するドア情報が見つかりませんでした。");
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
        
        {/* ★UI変更: 路線名セレクトボックスを先に配置 */}
        <div className="form-control w-full max-w-[140px]">
          <label className="label-text">路線</label>
          <select 
            className="select select-bordered select-sm"
            value={line}
            onChange={(e) => setLine(e.target.value)}
            disabled={lineList.length === 0}
          >
            {lineList.length === 0 && <option>読み込み中...</option>}
            {lineList.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>

        {/* ★UI変更: 駅名セレクトボックスをその後に配置 */}
        <div className="form-control w-full max-w-[140px]">
          <label className="label-text">駅</label>
          <select 
            className="select select-bordered select-sm"
            value={station}
            onChange={(e) => setStation(e.target.value)}
            disabled={isStationLoading || stationList.length === 0}
          >
            {isStationLoading ? (
              <option>駅を読込中...</option>
            ) : stationList.length === 0 ? (
              <option>駅なし</option>
            ) : (
              stationList.map(s => <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* 号車番号 */}
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

        {/* 検索ボタン */}
        <button type="submit" className="btn btn-primary btn-sm" disabled={isLoading || !line || !station}>
          {isLoading ? '検索中...' : '検索'}
        </button>
      </form>

      {/* --- 結果表示エリア --- */}
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