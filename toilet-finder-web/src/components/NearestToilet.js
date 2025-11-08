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
        console.log("検知された現在地:", latitude, longitude);

        try {
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(
              `${API_BASE_URL}/api/nearest?lat=${latitude}&lon=${longitude}`
            );
          
          if (response.status === 404) {
             setError("この周辺にトイレが見つかりませんでした。");
             setNearestToilet(null);
             return;
          }

          if (!response.ok) {
            throw new Error(`APIエラー: ${response.status}`);
          }
          
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
      {
        enableHighAccuracy: true, 
        timeout: 5000,             
      }
    );
  }, []); 

  if (isLoading) {
    return (
      <div className="p-4 text-center">
        <p className="text-xl font-bold">現在地から最寄りのトイレを検索中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700">
        <h2 className="text-lg font-bold">🚨 検索エラー</h2>
        <p>{error}</p>
        <p className="text-sm mt-2">（場所を変えて再度アクセスするか、地図から探してください。）</p>
      </div>
    );
  }

  if (nearestToilet) {
    const distanceText = formatDistance(nearestToilet.distance_meters);
    
    return (
      <div className="p-6 bg-white shadow-lg rounded-lg">
        <h2 className="text-2xl font-extrabold text-blue-600 mb-4">🚽 すぐそこ！最寄りのトイレ</h2>
        <div className="border-l-4 border-blue-500 pl-3">
          <p className="text-xl font-bold">
            {nearestToilet.name} 
            {distanceText && <span className="text-red-500 ml-2">({distanceText})</span>}
          </p>
          <p className="text-gray-600">{nearestToilet.address}</p>
        </div>
        
        <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
          <p className={nearestToilet.is_wheelchair_accessible ? "text-green-600" : "text-gray-400"}>
            車椅子: {nearestToilet.is_wheelchair_accessible ? '✅ 対応' : '❌ 非対応'}
          </p>
          <p className={nearestToilet.has_diaper_changing_station ? "text-green-600" : "text-gray-400"}>
            おむつ台: {nearestToilet.has_diaper_changing_station ? '✅ 対応' : '❌ 非対応'}
          </p>
          <p className={nearestToilet.is_ostomate_accessible ? "text-green-600" : "text-gray-400"}>
            オストメイト: {nearestToilet.is_ostomate_accessible ? '✅ 対応' : '❌ 非対応'}
          </p>
        </div>
        
        <div className="mt-4 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-gray-700 text-sm">
            {nearestToilet.opening_hours && `時間: ${nearestToilet.opening_hours}`}
          </p>
          {/* ★URLを修正しました★ */}
          <a 
            href={`https://www.google.com/maps/dir/?api=1&destination=${nearestToilet.latitude},${nearestToilet.longitude}`}
            target="_blank" 
            rel="noopener noreferrer" 
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-200 w-full sm:w-auto text-center"
          >
            Googleマップでルート案内 🏃‍♂️
          </a>
        </div>

      </div>
    );
  }

  return null; 
}