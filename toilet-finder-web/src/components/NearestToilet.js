"use client";

import { useState, useEffect } from 'react';

// 距離を整形するヘルパー関数
const formatDistance = (meters) => {
  if (typeof meters !== 'number' || isNaN(meters)) return '';
  if (meters < 1000) {
    // 1000m未満はメートルで表示
    return `${Math.round(meters)}m`;
  }
  // 1km以上はkm表示（小数点第1位まで）
  return `${(meters / 1000).toFixed(1)}km`;
};

export default function NearestToilet() {
  const [nearestToilet, setNearestToilet] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 1. 位置情報サービスが利用可能かチェック
    if (!navigator.geolocation) {
      setError('お使いの端末は位置情報取得に対応していません。');
      setIsLoading(false);
      return;
    }

    // 2. 現在地の取得を開始
    navigator.geolocation.getCurrentPosition(
      // 成功時のコールバック
      async (position) => {
        const { latitude, longitude } = position.coords;

        try {
          // 3. FastAPIの最寄り検索APIを呼び出す
          const response = await fetch(
            `/api/nearest?lat=${latitude}&lon=${longitude}`
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
      // 失敗時のコールバック
      (geoError) => {
        setIsLoading(false);
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setError('現在地の取得が拒否されました。設定を許可してください。');
        } else {
          setError('現在地の取得に失敗しました。');
        }
      },
      // オプション設定
      {
        enableHighAccuracy: true, 
        timeout: 5000,             
      }
    );
  }, []); 

  // -----------------------------------------------------------------
  // 画面表示
  // -----------------------------------------------------------------
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
        
        {/* ★★★ 修正箇所: grid-cols-2 -> grid-cols-3 ★★★ */}
        <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
          {/* アクセシビリティ情報を表示 */}
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
        
        {/* 時間とナビゲーション（別の行に表示） */}
        <div className="mt-4 flex justify-between items-center">
          <p className="text-gray-700 text-sm">
            {nearestToilet.opening_hours && `時間: ${nearestToilet.opening_hours}`}
          </p>
          <a 
            href={`http://googleusercontent.com/maps/google.com/1{nearestToilet.latitude},${nearestToilet.longitude}`} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-200"
          >
            Googleマップでルート案内 
          </a>
        </div>

      </div>
    );
  }

  return null; 
}