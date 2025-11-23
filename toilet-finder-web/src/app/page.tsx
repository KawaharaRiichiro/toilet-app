"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import Link from 'next/link';

// コンポーネントを動的インポート
const NearestToilet = dynamic(() => import('@/components/NearestToilet'), { 
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-gray-500">地図読み込み中...</div>
});
const InTrainSearch = dynamic(() => import('@/components/InTrainSearch'), { ssr: false });
const ToiletMap = dynamic(() => import("@/components/map"), { 
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-gray-500">地図読み込み中...</div>
});

// 型定義
type ToiletData = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  is_station_toilet: boolean;
  is_wheelchair_accessible: boolean;
  has_diaper_changing_station: boolean;
  is_ostomate_accessible: boolean;
  distance?: number;
};

// 距離フォーマット
const formatDistance = (meters?: number) => {
  if (!meters) return '';
  if (meters < 1000) return `${Math.round(meters)}m`;
  return `${(meters / 1000).toFixed(1)}km`;
};

export default function Home() {
  const [activeTab, setActiveTab] = useState<'current' | 'train' | 'map'>('current');
  const [nearestInfo, setNearestInfo] = useState<ToiletData | null>(null);

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
      <header className="navbar bg-white text-gray-800 shadow-sm z-20 border-b border-gray-200">
        <div className="flex-1">
          <span className="text-lg font-bold px-4">🚽 すぐそこトイレ</span>
        </div>
        {/* ★修正: 管理者リンクを削除しました */}
      </header>

      {/* コントロールパネル */}
      <div className="flex flex-col z-10 shadow-sm bg-white">
        
        {/* タブ切り替え */}
        <div className="px-4 py-3 bg-gray-100">
          <div className="flex p-1 bg-gray-200 rounded-lg">
            <button 
              className={`flex-1 py-2 text-sm font-bold rounded-md transition-all duration-200 ${
                activeTab === 'current' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('current')}
            >
              📍 現在地から
            </button>
            <button 
              className={`flex-1 py-2 text-sm font-bold rounded-md transition-all duration-200 ${
                activeTab === 'train' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('train')}
            >
              🚃 乗車中から
            </button>
            <button 
              className={`flex-1 py-2 text-sm font-bold rounded-md transition-all duration-200 ${
                activeTab === 'map' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('map')}
            >
              🗺️ 地図から
            </button>
          </div>
        </div>

        {/* 最寄りトイレ情報パネル (現在地タブかつデータがある時のみ) */}
        {activeTab === 'current' && nearestInfo && (
          <div className="px-4 py-3 bg-white border-b border-gray-200 animate-fade-in">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="text-xs text-gray-500 font-bold mb-1">▼ 一番近いトイレ</div>
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  {nearestInfo.is_station_toilet && "🚉"}
                  {nearestInfo.name}
                  <span className="text-red-500 text-base ml-2">
                    {formatDistance(nearestInfo.distance)}
                  </span>
                </h2>
                <p className="text-xs text-gray-500 mt-1">{nearestInfo.address}</p>
              </div>
              
              {/* ルート案内ボタン */}
              <a 
                 href={`https://www.google.com/maps/dir/?api=1&destination=${nearestInfo.latitude},${nearestInfo.longitude}`}
                 target="_blank" 
                 rel="noopener noreferrer" 
                 className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2 px-4 rounded-full shadow-md no-underline flex items-center"
              >
                 ルート案内 
              </a>
            </div>
            
            {/* 属性アイコン */}
            <div className="flex gap-2 mt-2">
               {nearestInfo.is_wheelchair_accessible && <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded border border-blue-200">♿ 車椅子</span>}
               {nearestInfo.has_diaper_changing_station && <span className="px-2 py-0.5 text-xs bg-pink-100 text-pink-800 rounded border border-pink-200">👶 おむつ</span>}
               {nearestInfo.is_ostomate_accessible && <span className="px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded border border-green-200">✚ オストメイト</span>}
            </div>
          </div>
        )}

        {/* 共通フィルター (乗車中以外で表示) */}
        {activeTab !== 'train' && (
          <div className="px-4 py-2 bg-white border-b border-gray-200 overflow-x-auto whitespace-nowrap">
              <div className="flex items-center gap-6">
               {/* 設備 */}
               <div className="flex items-center gap-2">
                 <span className="text-xs font-bold text-gray-500">設備:</span>
                 <div className="flex gap-2">
                   <label className="cursor-pointer flex items-center gap-1 px-2 py-1 rounded border border-gray-300 hover:bg-gray-50 transition">
                     <input type="checkbox" className="checkbox checkbox-xs checkbox-primary" checked={filters.wheelchair} onChange={() => handleCheckboxChange('wheelchair')} />
                     <span className="text-xs font-bold text-gray-700">♿ 車椅子</span>
                   </label>
                   <label className="cursor-pointer flex items-center gap-1 px-2 py-1 rounded border border-gray-300 hover:bg-gray-50 transition">
                     <input type="checkbox" className="checkbox checkbox-xs checkbox-secondary" checked={filters.diaper} onChange={() => handleCheckboxChange('diaper')} />
                     <span className="text-xs font-bold text-gray-700">👶 おむつ</span>
                   </label>
                   <label className="cursor-pointer flex items-center gap-1 px-2 py-1 rounded border border-gray-300 hover:bg-gray-50 transition">
                     <input type="checkbox" className="checkbox checkbox-xs checkbox-accent" checked={filters.ostomate} onChange={() => handleCheckboxChange('ostomate')} />
                     <span className="text-xs font-bold text-gray-700">✚ オストメイト</span>
                   </label>
                 </div>
               </div>

               {/* 場所 */}
               <div className="flex items-center gap-2 border-l pl-4">
                 <span className="text-xs font-bold text-gray-500">場所:</span>
                 <div className="flex rounded-md shadow-sm" role="group">
                   <button 
                     className={`px-3 py-1 text-xs font-bold border ${filters.inside_gate === null ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'} rounded-l-md`}
                     onClick={() => handleGateFilterChange(null)}
                   >全て</button>
                   <button 
                     className={`px-3 py-1 text-xs font-bold border-t border-b border-r ${filters.inside_gate === true ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                     onClick={() => handleGateFilterChange(true)}
                   >改札内</button>
                   <button 
                     className={`px-3 py-1 text-xs font-bold border-t border-b border-r ${filters.inside_gate === false ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'} rounded-r-md`}
                     onClick={() => handleGateFilterChange(false)}
                   >改札外</button>
                 </div>
               </div>
             </div>
          </div>
        )}
      </div>

      {/* メインコンテンツ */}
      <div className="flex-1 relative overflow-hidden">
        {activeTab === 'current' && (
          <div className="absolute inset-0">
            <ToiletMap 
              filters={filters} 
              onUpdateNearest={(data: ToiletData | null) => setNearestInfo(data)} 
            />
          </div>
        )}
        
        {activeTab === 'train' && (
          <div className="absolute inset-0 overflow-y-auto bg-gray-50 pb-20">
            <InTrainSearch />
          </div>
        )}

        {activeTab === 'map' && (
          <div className="absolute inset-0">
            <ToiletMap filters={filters} />
          </div>
        )}
      </div>
    </div>
  );
}