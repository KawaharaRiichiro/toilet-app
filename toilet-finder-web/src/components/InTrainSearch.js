"use client";

import { useState, useEffect } from 'react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

export default function InTrainSearch() {
  // 検索条件
  const [line, setLine] = useState('');       
  const [station, setStation] = useState(''); 
  const [direction, setDirection] = useState(''); // 方面
  const [car, setCar] = useState('5'); // デフォルト5号車

  const [lineList, setLineList] = useState([]);
  const [stationList, setStationList] = useState([]);
  const [directionList, setDirectionList] = useState([]);

  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const supabase = createClientComponentClient();

  // 1. 路線リスト取得
  useEffect(() => {
    const fetchLines = async () => {
      const { data, error } = await supabase
        .from('station_platform_doors')
        .select('line_name');
      
      if (!error && data) {
        const uniqueLines = [...new Set(data.map(item => item.line_name))];
        setLineList(uniqueLines);
        if (uniqueLines.length > 0) setLine(uniqueLines[0]);
      }
    };
    fetchLines();
  }, [supabase]);

  // 2. 駅リスト取得
  useEffect(() => {
    if (!line) return;
    const fetchStations = async () => {
      const { data, error } = await supabase
        .from('station_platform_doors')
        .select('station_name')
        .eq('line_name', line);

      if (!error && data) {
        const uniqueStations = [...new Set(data.map(item => item.station_name))];
        setStationList(uniqueStations);
        if (uniqueStations.length > 0) setStation(uniqueStations[0]);
        else setStation('');
      }
    };
    fetchStations();
  }, [line, supabase]);

  // 3. 方面リスト取得
  useEffect(() => {
    if (!line || !station) {
      setDirectionList([]);
      setDirection('');
      return;
    }
    const fetchDirections = async () => {
      const { data, error } = await supabase
        .from('station_platform_doors')
        .select('direction')
        .eq('line_name', line)
        .eq('station_name', station);

      if (!error && data) {
        const uniqueDirs = [...new Set(data.map(item => item.direction).filter(d => d))];
        setDirectionList(uniqueDirs);
        if (uniqueDirs.length > 0) setDirection(uniqueDirs[0]);
        else setDirection('');
      }
    };
    fetchDirections();
  }, [line, station, supabase]);

  // 4. 検索実行
  const handleSearch = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // ドアデータを検索
      let query = supabase
        .from('station_platform_doors')
        .select('nearest_toilet_id')
        .eq('line_name', line)
        .eq('station_name', station)
        .eq('car_number', parseInt(car));
      
      if (direction) {
        query = query.eq('direction', direction);
      }

      const { data: doorData, error: doorError } = await query.maybeSingle();

      if (doorError) throw doorError;
      if (!doorData || !doorData.nearest_toilet_id) {
        throw new Error("この場所の情報はまだ登録されていません");
      }

      // トイレ情報を取得
      const { data: toiletData, error: toiletError } = await supabase
        .from('toilets')
        .select('*')
        .eq('id', doorData.nearest_toilet_id)
        .single();

      if (toiletError) throw toiletError;
      
      setResult(toiletData);

    } catch (err) {
      console.error(err);
      setError(err.message || "検索に失敗しました");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 w-full">
      
      {/* 検索フォーム */}
      <div className="bg-white p-3 rounded-xl shadow-sm border border-gray-200">
        
        <div className="flex flex-col gap-3">
          {/* 1行目：路線と駅 */}
          <div className="grid grid-cols-2 gap-2">
            <div className="form-control w-full">
              <label className="label py-0 pb-1">
                <span className="label-text text-xs font-bold text-gray-500">路線</span>
              </label>
              <select 
                className="select select-bordered select-sm w-full font-bold text-gray-700" 
                value={line} 
                onChange={(e) => setLine(e.target.value)}
              >
                {lineList.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>

            <div className="form-control w-full">
              <label className="label py-0 pb-1">
                <span className="label-text text-xs font-bold text-gray-500">駅</span>
              </label>
              <select 
                className="select select-bordered select-sm w-full font-bold text-gray-700" 
                value={station} 
                onChange={(e) => setStation(e.target.value)}
                disabled={!stationList.length}
              >
                {stationList.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          {/* 2行目：方面と号車 */}
          <div className="grid grid-cols-2 gap-2">
            {/* 方面 */}
            {directionList.length > 0 ? (
              <div className="form-control w-full">
                <label className="label py-0 pb-1">
                  <span className="label-text text-xs font-bold text-gray-500">方面</span>
                </label>
                <select 
                  className="select select-bordered select-sm w-full font-bold text-gray-700" 
                  value={direction} 
                  onChange={(e) => setDirection(e.target.value)}
                >
                  {directionList.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            ) : (
              <div className="hidden"></div>
            )}

            <div className="form-control w-full">
              <label className="label py-0 pb-1">
                <span className="label-text text-xs font-bold text-gray-500">乗車位置</span>
              </label>
              <select 
                className={`select select-bordered select-sm w-full font-bold text-gray-700`}
                value={car} 
                onChange={(e) => setCar(e.target.value)}
              >
                {[...Array(15)].map((_, i) => (
                  <option key={i + 1} value={i + 1}>{i + 1}号車</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* ★修正: 青背景を強制指定して視認性を確保 */}
        <button 
          className="btn bg-blue-600 hover:bg-blue-700 text-white border-none btn-sm w-full font-bold mt-4 shadow-sm"
          onClick={handleSearch}
          disabled={isLoading || !line || !station}
        >
          {isLoading ? <span className="loading loading-spinner loading-xs"></span> : "トイレを探す"}
        </button>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="alert alert-error mt-4 text-sm py-2 rounded-lg text-white">
          <span>{error}</span>
        </div>
      )}

      {/* 検索結果 */}
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

              <a 
                href={`https://www.google.com/maps/dir/?api=1&destination=${result.latitude},${result.longitude}`}
                target="_blank" 
                rel="noopener noreferrer" 
                className="btn bg-blue-600 hover:bg-blue-700 text-white border-none btn-sm w-full no-underline"
              >
                ルート案内
              </a>
          </div>
        </div>
      )}
    </div>
  );
}