"use client";

import { useState } from "react";
import ToiletMap from "@/components/map";
import NearestToilet from "@/components/NearestToilet";
import InTrainSearch from "@/components/InTrainSearch";

export default function Home() {
  const [activeTab, setActiveTab] = useState<'current' | 'train'>('current');

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
      <header className="navbar bg-primary text-primary-content shadow-md z-20">
        <div className="flex-1">
          <span className="text-xl font-bold px-4">🚽 トイレ探索アプリ　すぐそこトイレ</span>
        </div>
      </header>

      {/* コントロールパネル */}
      <div className="flex flex-col z-10 shadow-md bg-base-100">
        
        {/* タブ切り替え */}
        <div className="p-3 bg-base-200">
          <div role="tablist" className="tabs tabs-boxed bg-gray-300 p-1">
            <a 
              role="tab" 
              className={`tab flex-1 transition-all duration-200 font-bold text-base ${activeTab === 'current' ? 'tab-active bg-white text-primary shadow-sm' : 'text-gray-600'}`}
              onClick={() => setActiveTab('current')}
            >
              📍 現在地から
            </a>
            <a 
              role="tab" 
              className={`tab flex-1 transition-all duration-200 font-bold text-base ${activeTab === 'train' ? 'tab-active bg-white text-primary shadow-sm' : 'text-gray-600'}`}
              onClick={() => setActiveTab('train')}
            >
              🚃 乗車中から
            </a>
          </div>
        </div>

        {/* タブの中身 */}
        <div className="bg-white border-b border-base-300">
          {activeTab === 'current' && (
            <div className="p-4 bg-yellow-50 animation-fade-in">
              <NearestToilet />
            </div>
          )}
          {activeTab === 'train' && (
             <div className="p-4 bg-blue-50 animation-fade-in">
              <InTrainSearch />
            </div>
          )}
        </div>

        {/* 共通フィルター */}
        <div className="bg-base-100 p-3 overflow-x-auto whitespace-nowrap">
          <div className="flex items-center gap-6">
            
            {/* 設備フィルター */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-gray-500">設備:</span>
              <div className="flex gap-2">
                <label className="cursor-pointer label border border-gray-300 rounded-lg px-3 py-1 hover:bg-base-200 transition bg-white">
                  <span className="label-text font-medium mr-2 text-gray-700">♿ 車椅子</span>
                  <input type="checkbox" className="checkbox checkbox-sm checkbox-primary" checked={filters.wheelchair} onChange={() => handleCheckboxChange('wheelchair')} />
                </label>
                <label className="cursor-pointer label border border-gray-300 rounded-lg px-3 py-1 hover:bg-base-200 transition bg-white">
                  <span className="label-text font-medium mr-2 text-gray-700">👶 おむつ</span>
                  <input type="checkbox" className="checkbox checkbox-sm checkbox-primary" checked={filters.diaper} onChange={() => handleCheckboxChange('diaper')} />
                </label>
                <label className="cursor-pointer label border border-gray-300 rounded-lg px-3 py-1 hover:bg-base-200 transition bg-white">
                  <span className="label-text font-medium mr-2 text-gray-700">✚ オストメイト</span>
                  <input type="checkbox" className="checkbox checkbox-sm checkbox-primary" checked={filters.ostomate} onChange={() => handleCheckboxChange('ostomate')} />
                </label>
              </div>
            </div>

            <div className="divider divider-horizontal mx-0"></div>

            {/* 場所フィルター (インラインスタイルで文字色を強制) */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-gray-500">場所:</span>
              <div className="join border border-gray-300 bg-white rounded-lg overflow-hidden">
                {/* 全て */}
                <button 
                  className={`join-item btn btn-sm px-4 font-medium transition-colors duration-200 ${filters.inside_gate === null ? 'bg-primary border-primary' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  style={filters.inside_gate === null ? { color: 'white' } : {}}
                  onClick={() => handleGateFilterChange(null)}
                >
                  全て
                </button>
                {/* 改札内 */}
                <button 
                  className={`join-item btn btn-sm px-4 font-medium transition-colors duration-200 ${filters.inside_gate === true ? 'bg-primary border-primary' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  style={filters.inside_gate === true ? { color: 'white' } : {}}
                  onClick={() => handleGateFilterChange(true)}
                >
                  改札内
                </button>
                {/* 改札外 */}
                <button 
                  className={`join-item btn btn-sm px-4 font-medium transition-colors duration-200 ${filters.inside_gate === false ? 'bg-primary border-primary' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  style={filters.inside_gate === false ? { color: 'white' } : {}}
                  onClick={() => handleGateFilterChange(false)}
                >
                  改札外
                </button>
              </div>
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