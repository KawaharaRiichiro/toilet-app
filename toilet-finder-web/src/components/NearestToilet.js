"use client";

import { useState, useEffect } from 'react';

const formatDistance = (meters) => {
  if (typeof meters !== 'number' || isNaN(meters)) return '';
  if (meters < 1000) return `${Math.round(meters)}m`;
  return `${(meters / 1000).toFixed(1)}km`;
};

export default function NearestToilet() {
  const [nearestToilet, setNearestToilet] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError('お使いの端末は位置情報取得に対応していません。');
      setIsLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_BASE_URL}/api/nearest?lat=${latitude}&lon=${longitude}`);
          
          if (response.status === 404) {
             setError("この周辺にトイレが見つかりませんでした。");
             setNearestToilet(null);
             return;
          }
          if (!response.ok) throw new Error(`APIエラー: ${response.status}`);
          const data = await response.json();
          setNearestToilet(data);
        } catch (apiError) {
          console.error("API呼び出しエラー:", apiError);
          setError('サーバーからトイレ情報を取得できませんでした。');
        } finally {
          setIsLoading(false);
        }
      },
      (geoError) => {
        setIsLoading(false);
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setError('現在地の取得が拒否されました。設定を許可してください。');
        } else {
          setError('現在地の取得に失敗しました。');
        }
      },
      { enableHighAccuracy: true, timeout: 5000 }
    );
  }, []); 

  if (isLoading) {
    return (
      <div className="p-8 text-center flex flex-col items-center justify-center gap-3 text-gray-500">
        <span className="loading loading-spinner loading-lg text-primary"></span>
        <p className="font-bold animate-pulse">現在地から最寄りのトイレを検索中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-start gap-3">
        <span className="text-2xl">🚨</span>
        <div>
            <h2 className="text-lg font-bold">検索エラー</h2>
            <p className="font-medium">{error}</p>
            <p className="text-xs mt-1 opacity-80">（場所を変えて再度アクセスするか、地図から探してください）</p>
        </div>
      </div>
    );
  }

  if (nearestToilet) {
    const distanceText = formatDistance(nearestToilet.distance_meters);
    
    return (
      <div className="p-5 bg-white shadow-sm rounded-xl border border-yellow-200">
        <h2 className="text-xl font-extrabold text-yellow-600 mb-4 flex items-center gap-2">
          <span>🏃‍♂️</span> すぐそこ！最寄りのトイレ
        </h2>
        <div className="border-l-4 border-yellow-500 pl-4 py-1 bg-yellow-50 rounded-r-lg">
          <div className="text-xl font-bold text-gray-900">
            {nearestToilet.name} 
            {distanceText && <span className="text-red-500 ml-2 text-base">({distanceText})</span>}
          </div>
          <p className="text-gray-600 text-sm mt-1">{nearestToilet.address}</p>
        </div>
        
        <div className="mt-4 flex flex-wrap gap-2">
             <span className={`badge ${nearestToilet.is_wheelchair_accessible ? "badge-success text-white" : "badge-ghost text-gray-400"}`}>
                 ♿ 車椅子{nearestToilet.is_wheelchair_accessible ? 'OK' : 'NG'}
             </span>
             <span className={`badge ${nearestToilet.has_diaper_changing_station ? "badge-success text-white" : "badge-ghost text-gray-400"}`}>
                 👶 おむつ{nearestToilet.has_diaper_changing_station ? 'OK' : 'NG'}
             </span>
             <span className={`badge ${nearestToilet.is_ostomate_accessible ? "badge-success text-white" : "badge-ghost text-gray-400"}`}>
                 ✚ オストメイト{nearestToilet.is_ostomate_accessible ? 'OK' : 'NG'}
             </span>
        </div>
        
        <div className="mt-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
           {nearestToilet.opening_hours ? (
             <p className="text-gray-600 text-sm flex items-center gap-1">
               <span>🕘</span> 時間: {nearestToilet.opening_hours}
             </p>
           ) : <div></div>}
           
          {/* ★修正: ボタンのスタイルを直接指定し、URLも修正 */}
          <a 
            href={`https://www.google.com/maps/dir/?api=1&destination=${nearestToilet.latitude},${nearestToilet.longitude}`}
            target="_blank" 
            rel="noopener noreferrer" 
            className="py-2 px-6 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg flex items-center gap-2 no-underline transition-colors shadow-sm"
          >
            <span className="text-xl">🗺️</span>
            <span>ルート案内</span>
          </a>
        </div>
      </div>
    );
  }
  return null; 
}