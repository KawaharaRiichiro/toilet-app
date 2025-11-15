"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import Link from 'next/link';

// コンポーネントの動的インポート
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
      <header className="navbar bg-primary text-primary-content shadow-md z-20">
        <div className="flex-1">
          <span className="text-xl font-bold px-4">🚽 トイレ探索アプリ　すぐそこトイレ</span>
        </div>
        <div className="flex-none">
           <Link href="/login" className="btn btn-ghost btn-sm text-white">
             管理者
           </Link>
        </div>
      </header>

      {/* コントロールパネル */}
      <div className="flex flex-col z-10 shadow-md bg-base-100">
        
        {/* タブ切り替え */}
        <div className="p-3 bg-base-200">
          <div role="tablist" className="tabs tabs-boxed grid grid-cols-3 gap-2">
            <button 
              role="tab" 
              className={`tab font-bold transition-all duration-200 ${activeTab === 'current' ? 'tab-active bg-primary text-primary-content shadow' : 'bg-base-100'}`}
              onClick={() => setActiveTab('current')}
            >
              📍 現在地から
            </button>
            <button 
              role="tab" 
              className={`tab font-bold transition-all duration-200 ${activeTab === 'train' ? 'tab-active bg-primary text-primary-content shadow' : 'bg-base-100'}`}
              onClick={() => setActiveTab('train')}
            >
              🚃 乗車中から
            </button>
            <button 
              role="tab" 
              className={`tab font-bold transition-all duration-200 ${activeTab === 'map' ? 'tab-active bg-primary text-primary-content shadow' : 'bg-base-100'}`}
              onClick={() => setActiveTab('map')}
            >
              🗺️ 地図から
            </button>
          </div>
        </div>

        {/* 最寄りトイレ情報パネル */}
        {activeTab === 'current' && nearestInfo && (
          <div className="bg-white p-3 border-b border-gray-200 animate-fade-in">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="text-xs text-gray-500 font-bold mb-1">▼ すぐそこ！最寄りのトイレ</div>
                <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                  {nearestInfo.is_station_toilet && "🚉"}
                  {nearestInfo.name}
                  <span className="text-red-500 text-sm ml-2 font-bold">
                    {formatDistance(nearestInfo.distance)}
                  </span>
                </h2>
                <p className="text-xs text-gray-500 mt-1">{nearestInfo.address}</p>
              </div>
              
              <a 
                 href={`https://www.google.com/maps/dir/?api=1&destination=${nearestInfo.latitude},${nearestInfo.longitude}`}
                 target="_blank" 
                 rel="noopener noreferrer" 
                 className="btn btn-primary btn-sm text-white no-underline shadow"
              >
                 ルート案内 
              </a>
            </div>
            
            <div className="flex gap-2 mt-1">
               {nearestInfo.is_wheelchair_accessible && <span className="badge badge-sm badge-outline text-blue-600 border-blue-600">♿ 車椅子</span>}
               {nearestInfo.has_diaper_changing_station && <span className="badge badge-sm badge-outline text-pink-600 border-pink-600">👶 おむつ</span>}
               {nearestInfo.is_ostomate_accessible && <span className="badge badge-sm badge-outline text-green-600 border-green-600">✚ オストメイト</span>}
            </div>
          </div>
        )}

        {/* 共通フィルター */}
        {activeTab !== 'train' && (
          <div className="bg-base-100 p-3 overflow-x-auto whitespace-nowrap border-b border-base-200">
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

               {/* 場所フィルター */}
               <div className="flex items-center gap-2 border-l pl-4">
                 <span className="text-sm font-bold text-gray-500">場所:</span>
                 <div className="join">
                   <button 
                     className={`join-item btn btn-sm px-4 font-medium transition-colors duration-200 ${filters.inside_gate === null ? 'bg-blue-600 hover:bg-blue-700 !text-white border-blue-600' : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'}`}
                     onClick={() => handleGateFilterChange(null)}
                   >
                     全て
                   </button>
                   <button 
                     className={`join-item btn btn-sm px-4 font-medium transition-colors duration-200 ${filters.inside_gate === true ? 'bg-blue-600 hover:bg-blue-700 !text-white border-blue-600' : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'}`}
                     onClick={() => handleGateFilterChange(true)}
                   >
                     改札内
                   </button>
                   <button 
                     className={`join-item btn btn-sm px-4 font-medium transition-colors duration-200 ${filters.inside_gate === false ? 'bg-blue-600 hover:bg-blue-700 !text-white border-blue-600' : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'}`}
                     onClick={() => handleGateFilterChange(false)}
                   >
                     改札外
                   </button>
                 </div>
               </div>
             </div>
          </div>
        )}
      </div>

      {/* メインコンテンツ */}
      <div className="flex-1 relative overflow-hidden">
        {activeTab === 'current' && (
          <NearestToilet 
            filters={filters} 
            onUpdateNearest={(data: ToiletData | null) => setNearestInfo(data)} 
          />
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