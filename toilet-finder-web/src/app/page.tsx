"use client";

import { useState } from "react";
import ToiletMap from "@/components/map";
import NearestToilet from "@/components/NearestToilet";
import InTrainSearch from "@/components/InTrainSearch"; // インポート

export default function Home() {

  // フィルターの状態
// 修正案1
  const [filters, setFilters] = useState({
    wheelchair: false,
    diaper: false,
    ostomate: false,
    inside_gate: null as boolean | null, // ← 「boolean または null だよ」と明示
  });

  // 改札内/外/全て ラジオボタン用の状態変更関数
  const handleGateFilterChange = (value: boolean | null) => {
    setFilters(prev => ({
      ...prev,
      inside_gate: value
    }));
  };

  // 既存のチェックボックス用の状態変更関数
  const handleCheckboxChange = (key: 'wheelchair' | 'diaper' | 'ostomate') => {
    setFilters(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  return (
    <div className="flex flex-col h-screen">

      {/* 1. ヘッダー (変更なし) */}
      <header>
        <div className="navbar bg-base-100 shadow-lg">
          <div className="flex-1">
            <a className="btn btn-ghost text-xl">トイレを探すアプリ</a>
          </div>
        </div>
      </header>

      {/* 2. 最寄りトイレ即時表示ペイン (変更なし) */}
      <div className="bg-yellow-50 p-4 border-b border-yellow-200">
        <NearestToilet />
      </div>

      {/* 3. フィルターUIエリア (変更なし) */}
      <div className="bg-base-100 p-3 flex flex-wrap overflow-x-auto items-center gap-4">
        {/* ... (チェックボックスとラジオボタン) ... */}
        
        {/* --- 1. 車いす --- */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="checkbox checkbox-primary"
            checked={filters.wheelchair}
            onChange={() => handleCheckboxChange('wheelchair')}
          />
          <span className="label-text whitespace-nowrap">♿ 車いす</span>
        </label>

        {/* --- 2. おむつ台 --- */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="checkbox checkbox-primary"
            checked={filters.diaper}
            onChange={() => handleCheckboxChange('diaper')}
          />
          <span className="label-text whitespace-nowrap">🚼 おむつ台</span>
        </label>

        {/* --- 3. オストメイト --- */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="checkbox checkbox-primary"
            checked={filters.ostomate}
            onChange={() => handleCheckboxChange('ostomate')}
          />
          <span className="label-text whitespace-nowrap">🚻 オストメイト</span>
        </label>

        {/* --- 4. 駅トイレ --- */}
        <div className="flex items-center gap-2">
          <span className="label-text whitespace-nowrap">🚇 駅トイレ:</span>
          {/* ラジオボタングループ */}
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name="gate-filter"
              className="radio radio-primary"
              checked={filters.inside_gate === true}
              onChange={() => handleGateFilterChange(true)}
            />
            <span>改札内</span>
          </label>
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name="gate-filter"
              className="radio radio-primary"
              checked={filters.inside_gate === false}
              onChange={() => handleGateFilterChange(false)}
            />
            <span>改札外</span>
          </label>
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name="gate-filter"
              className="radio radio-primary"
              checked={filters.inside_gate === null}
              onChange={() => handleGateFilterChange(null)}
            />
            <span>全て</span>
          </label>
        </div>
      </div>

      {/* ★★★ 修正箇所: 電車内検索ペインをここに移動 ★★★ */}
      <div className="bg-blue-50 p-4 border-t border-b border-blue-200">
        <InTrainSearch />
      </div>

      {/* 4. メインコンテンツ (地図) (変更なし) */}
      {/* flex-grow が指定されているため、地図が残りのスペースをすべて埋めます */}
      <main className="flex-grow">
        <ToiletMap filters={filters} />
      </main>
      
    </div>
  );
}