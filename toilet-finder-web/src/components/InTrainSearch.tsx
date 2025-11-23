"use client";

import React, { useState, useEffect } from 'react';
import { Train, ChevronRight, MapPin, Navigation, CheckCircle2 } from 'lucide-react';

// トイレの型定義
interface Toilet {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  is_station_toilet: boolean;
  is_wheelchair_accessible: boolean;
  has_diaper_changing_station: boolean;
  is_ostomate_accessible: boolean;
}

export default function InTrainSearch() {
  // 選択状態
  const [line, setLine] = useState('');       
  const [station, setStation] = useState(''); 
  const [direction, setDirection] = useState(''); 
  const [car, setCar] = useState(''); 

  // リストデータ
  const [lineList, setLineList] = useState<string[]>([]);
  const [stationList, setStationList] = useState<string[]>([]);
  const [directionList, setDirectionList] = useState<string[]>([]);
  const [carList, setCarList] = useState<number[]>([]);

  // 結果
  const [result, setResult] = useState<Toilet | null>(null);
  const [loading, setLoading] = useState(false);

  // APIのベースURL
  const API_BASE = 'http://127.0.0.1:8000';

  // 1. 初回ロード: 路線リスト取得
  useEffect(() => {
    const fetchLines = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/train/lines`);
        if (res.ok) setLineList(await res.json());
      } catch (e) { console.error(e); }
    };
    fetchLines();
  }, []);

  // 2. 路線変更時: 駅リスト取得
  useEffect(() => {
    if (!line) { setStationList([]); return; }
    const fetchStations = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/train/stations?line=${encodeURIComponent(line)}`);
        if (res.ok) {
          setStationList(await res.json());
          setStation(''); setDirection(''); setCar(''); setResult(null);
        }
      } catch (e) { console.error(e); }
    };
    fetchStations();
  }, [line]);

  // 3. 駅変更時: 方面リスト取得
  useEffect(() => {
    if (!line || !station) { setDirectionList([]); return; }
    const fetchDirections = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/train/directions?line=${encodeURIComponent(line)}&station=${encodeURIComponent(station)}`);
        if (res.ok) {
          setDirectionList(await res.json());
          setDirection(''); setCar(''); setResult(null);
        }
      } catch (e) { console.error(e); }
    };
    fetchDirections();
  }, [station]);

  // 4. 方面変更時: 号車リスト取得
  useEffect(() => {
    if (!line || !station || !direction) { setCarList([]); return; }
    const fetchCars = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/train/cars?line=${encodeURIComponent(line)}&station=${encodeURIComponent(station)}&direction=${encodeURIComponent(direction)}`);
        if (res.ok) {
          setCarList(await res.json());
          setCar(''); setResult(null);
        }
      } catch (e) { console.error(e); }
    };
    fetchCars();
  }, [direction]);

  // 5. 検索実行
  const handleSearch = async () => {
    if (!line || !station || !direction || !car) return;
    setLoading(true);
    try {
      const query = `line=${encodeURIComponent(line)}&station=${encodeURIComponent(station)}&direction=${encodeURIComponent(direction)}&car=${car}`;
      const res = await fetch(`${API_BASE}/api/train/search?${query}`);
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        alert("該当するトイレが見つかりませんでした");
      }
    } catch (e) {
      console.error(e);
      alert("エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow-sm h-full overflow-y-auto">
      <h2 className="text-lg font-bold mb-4 text-gray-800 flex items-center gap-2">
        <Train className="h-5 w-5 text-blue-600" />
        乗車中から探す
      </h2>

      <div className="space-y-4">
        {/* 路線選択 */}
        <SelectBox 
          label="路線" 
          value={line} 
          onChange={setLine} 
          options={lineList} 
          placeholder="路線を選択"
        />

        {/* 駅選択 */}
        <SelectBox 
          label="今の駅 / 次の駅" 
          value={station} 
          onChange={setStation} 
          options={stationList} 
          disabled={!line}
          placeholder="駅を選択"
        />

        {/* 方面選択 */}
        <SelectBox 
          label="進行方向" 
          value={direction} 
          onChange={setDirection} 
          options={directionList} 
          disabled={!station}
          placeholder="方面を選択"
        />

        {/* 号車選択 */}
        <div className="form-control w-full">
          <label className="label">
            <span className="label-text font-bold text-gray-600 text-xs">乗っている車両 (号車)</span>
          </label>
          <select 
            className="select select-bordered w-full bg-white text-gray-800 disabled:bg-gray-100"
            value={car}
            onChange={(e) => setCar(e.target.value)}
            disabled={!direction}
          >
            <option value="">号車を選択</option>
            {carList.map(c => (
              <option key={c} value={c}>{c}号車</option>
            ))}
          </select>
        </div>

        <button
          onClick={handleSearch}
          disabled={!car || loading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md transition-all active:scale-95 disabled:bg-gray-300 disabled:scale-100 flex justify-center items-center gap-2"
        >
          {loading ? <span className="loading loading-spinner"></span> : <CheckCircle2 className="h-5 w-5" />}
          最適なトイレを案内する
        </button>
      </div>

      {/* 結果表示エリア */}
      {result && (
        <div className="mt-6 bg-white rounded-xl shadow-md border border-blue-100 overflow-hidden animate-fade-in">
          <div className="bg-blue-50 p-3 border-b border-blue-100">
            <div className="text-xs text-blue-800 font-bold">▼ あなたに最適なトイレ</div>
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
                className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold py-3 px-4 rounded-lg shadow-md flex items-center justify-center gap-2 transition-colors"
              >
                <Navigation className="h-4 w-4" />
                ここへ行く (ルート案内)
              </a>
          </div>
        </div>
      )}
    </div>
  );
}

// 汎用セレクトボックスコンポーネント
function SelectBox({ label, value, onChange, options, disabled = false, placeholder }: any) {
  return (
    <div className="form-control w-full">
      <label className="label">
        <span className="label-text font-bold text-gray-600 text-xs">{label}</span>
      </label>
      <select 
        className="select select-bordered w-full bg-white text-gray-800 disabled:bg-gray-100"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        <option value="">{placeholder}</option>
        {options.map((opt: string) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}