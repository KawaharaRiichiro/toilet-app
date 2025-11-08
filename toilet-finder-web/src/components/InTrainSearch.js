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
  const [station, setStation] = useState(''); 
  const [line, setLine] = useState('');       
  const [car, setCar] = useState('5');
  
  // ドロップダウン用リストの状態
  const [stationList, setStationList] = useState([]);
  const [lineList, setLineList] = useState([]);
  
  // APIの結果
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLineLoading, setIsLineLoading] = useState(false);

  // 1. コンポーネント読み込み時に「駅名リスト」を取得
  useEffect(() => {
    const fetchStations = async () => {
      try {
        const res = await fetch('/api/stations');
        
        // ★★★ 修正箇所: 成功したかチェック ★★★
        if (!res.ok) {
          throw new Error('駅リストのAPI取得に失敗しました');
        }
        
        const data = await res.json();
        
        // ★★★ 修正箇所: dataが配列であるか確認 ★★★
        if (Array.isArray(data)) {
          setStationList(data);
          if (data.length > 0) {
            setStation(data[0]); // リストの最初の駅をデフォルト選択
          }
        } else {
          throw new Error('APIが配列でないデータを返しました');
        }
        
      } catch (err) {
        console.error("駅リストの取得に失敗", err);
      }
    };
    fetchStations();
  }, []); // 空の配列[] = 読み込み時に1回だけ実行

  // 2. 「駅名」が変更されたら、その駅の「路線リスト」を取得
  useEffect(() => {
    if (!station) return; // 駅が未選択なら何もしない

    const fetchLines = async () => {
      setIsLineLoading(true);
      setLineList([]); // 路線リストをリセット
      try {
        const params = new URLSearchParams({ station: station });
        const res = await fetch(`/api/lines?${params.toString()}`);
        
        // ★★★ 修正箇所: 成功したかチェック ★★★
        if (!res.ok) {
          throw new Error('路線リストのAPI取得に失敗しました');
        }
        
        const data = await res.json();
        
        // ★★★ 修正箇所: dataが配列であるか確認 ★★★
        if (Array.isArray(data)) {
          setLineList(data);
          if (data.length > 0) {
            setLine(data[0]); // リストの最初の路線をデフォルト選択
          }
        } else {
          throw new Error('APIが配列でないデータを返しました');
        }
        
      } catch (err) {
        console.error("路線リストの取得に失敗", err);
      } finally {
        setIsLineLoading(false);
      }
    };
    
    fetchLines();
  }, [station]); // station の値が変わるたびに実行

  // 3. 検索ボタンが押された時の処理 (変更なし)
  const handleSearch = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const params = new URLSearchParams({
        station: station,
        line: line,
        car: car,
      });
      
      const response = await fetch(`/api/in-train-search?${params.toString()}`);
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '検索に失敗しました');
      }

      const data = await response.json();
      setResult(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-2">
      <h2 className="text-xl font-bold text-blue-800 mb-2">🚃 電車内検索 (次の駅)</h2>
      
      {/* 検索フォーム */}
      <form onSubmit={handleSearch} className="flex flex-wrap gap-2 items-end">
        
        {/* 駅名 (ドロップダウン) */}
        <div className="form-control">
          <label className="label-text">駅名</label>
          <select 
            value={station}
            onChange={(e) => setStation(e.target.value)}
            className="select select-bordered select-sm"
            disabled={stationList.length === 0}
          >
            {/* stationListが配列であることを前提とする */}
            {stationList.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* 路線名 (ドロップダウン) */}
        <div className="form-control">
          <label className="label-text">路線名</label>
          <select 
            value={line}
            onChange={(e) => setLine(e.target.value)}
            className="select select-bordered select-sm"
            disabled={isLineLoading || lineList.length === 0}
          >
            {isLineLoading ? (
              <option>読み込み中...</option>
            ) : (
              /* lineListが配列であることを前提とする */
              lineList.map(l => <option key={l} value={l}>{l}</option>)
            )}
          </select>
        </div>

        {/* 号車番号 (変更なし) */}
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

        {/* 検索ボタン (変更なし) */}
        <button type="submit" className="btn btn-primary btn-sm" disabled={isLoading}>
          {isLoading ? '検索中...' : '検索'}
        </button>
      </form>

      {/* --- 結果表示エリア (変更なし) --- */}
      {error && (
        <div className="mt-3 text-red-600">
          <strong>エラー:</strong> {error}
        </div>
      )}

      {result && (
        <div className="mt-3 p-3 bg-blue-100 rounded-lg">
          <h3 className="font-bold">✅ ドアから一番近いトイレ</h3>
          <p className="text-lg">
            {result.name} 
            <span className="text-red-600 font-bold ml-2">
              (ドアから {formatDistance(result.distance_meters)})
            </span>
          </p>
          <p className="text-sm text-gray-700">{result.address}</p>
        </div>
      )}

    </div>
  );
}