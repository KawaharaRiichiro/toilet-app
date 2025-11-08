"use client";

import { useState } from "react";
import ToiletMap from "@/components/map";
import NearestToilet from "@/components/NearestToilet";
import InTrainSearch from "@/components/InTrainSearch";

export default function Home() {
  // タブの状態管理 ('current' = 現在地から, 'train' = 乗車中から)
  const [activeTab, setActiveTab] = useState<'current' | 'train'>('current');

  // フィルターの状態
  const [filters, setFilters] = useState({
    wheelchair: false,
    diaper: false,
    ostomate: false,
    inside_gate: null as boolean | null,
  });

  const handleGateFilterChange = (value: boolean | null) => {
    setFilters(prev => ({ ...prev, inside_gate: value }));
  };

  const handleCheckboxChange = (key: 'wheelchair' | 'diaper' | 'ostomate') => {
    setFilters(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">

      {/* ヘッダー */}
      <header className="navbar bg-base-100 shadow-sm z-20">
        <div className="flex-1">
          <a className="btn btn-ghost text-xl text-primary">🚽 トイレ探索アプリ</a>
        </div>
      </header>

{/* コントロールパネル */}
      <div className="flex flex-col z-10 shadow-md bg-base-100"> {/* 背景色を明示 */}
        
        {/* タブ切り替え (tabs-lifted を使用) */}
        <div className="pt-2 px-2 bg-base-200"> {/*少し上と左右に余白を追加*/}
          <div role="tablist" className="tabs tabs-lifted">
            <a 
              role="tab" 
              className={`tab ${activeTab === 'current' ? 'tab-active [--tab-bg:white]' : ''} font-bold`}
              onClick={() => setActiveTab('current')}
            >
              📍 現在地から
            </a>
            <a 
              role="tab" 
              className={`tab ${activeTab === 'train' ? 'tab-active [--tab-bg:white]' : ''} font-bold`}
              onClick={() => setActiveTab('train')}
            >
              🚃 乗車中から
            </a>
          </div>
        </div>

        {/* タブの中身 (枠線を調整して一体感を出す) */}
        <div className="bg-white border-base-300 border-b-2 p-3 rounded-b-box"> {/* rounded-b-box で下の角を丸く */}
          {activeTab === 'current' && (
            <div className="animation-fade-in">
              <NearestToilet />
            </div>
          )}
          {activeTab === 'train' && (
             <div className="animation-fade-in">
              <InTrainSearch />
            </div>
          )}
        </div>

        {/* 共通フィルター */}
        <div className="bg-base-100 p-3 border-t border-base-200 overflow-x-auto">
          <div className="flex flex-wrap items-center gap-4">
            {/* 設備フィルター */}
            <div className="flex gap-2">
              <label className="cursor-pointer label border rounded-lg px-2 py-1 hover:bg-base-200 transition">
                <span className="label-text mr-2">♿ 車椅子</span>
                <input type="checkbox" className="checkbox checkbox-sm checkbox-primary" checked={filters.wheelchair} onChange={() => handleCheckboxChange('wheelchair')} />
              </label>
              <label className="cursor-pointer label border rounded-lg px-2 py-1 hover:bg-base-200 transition">
                <span className="label-text mr-2">👶 おむつ</span>
                <input type="checkbox" className="checkbox checkbox-sm checkbox-primary" checked={filters.diaper} onChange={() => handleCheckboxChange('diaper')} />
              </label>
              <label className="cursor-pointer label border rounded-lg px-2 py-1 hover:bg-base-200 transition">
                <span className="label-text mr-2">✚ オストメイト</span>
                <input type="checkbox" className="checkbox checkbox-sm checkbox-primary" checked={filters.ostomate} onChange={() => handleCheckboxChange('ostomate')} />
              </label>
            </div>

            {/* 場所フィルター */}
            <div className="join">
              <input className="join-item btn btn-sm" type="radio" name="gate" aria-label="全て" checked={filters.inside_gate === null} onChange={() => handleGateFilterChange(null)} />
              <input className="join-item btn btn-sm" type="radio" name="gate" aria-label="改札内" checked={filters.inside_gate === true} onChange={() => handleGateFilterChange(true)} />
              <input className="join-item btn btn-sm" type="radio" name="gate" aria-label="改札外" checked={filters.inside_gate === false} onChange={() => handleGateFilterChange(false)} />
            </div>
          </div>
        </div>
      </div>

      {/* 地図 */}
      <main className="flex-grow relative">
        <ToiletMap filters={filters} />
      </main>

    </div>
  );
}