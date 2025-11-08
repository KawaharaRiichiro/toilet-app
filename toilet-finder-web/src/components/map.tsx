"use client";

import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF } from "@react-google-maps/api";
import { useEffect, useState, useCallback } from "react";

// トイレデータの型定義
type Toilet = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  opening_hours: string | null;
  availability_notes: string | null;
  is_wheelchair_accessible: boolean;
  has_diaper_changing_station: boolean;
  is_ostomate_accessible: boolean;
  inside_gate: boolean | null;
};

// フィルターの型定義
type ToiletMapProps = {
  filters: {
    wheelchair: boolean;
    diaper: boolean;
    ostomate: boolean;
    inside_gate: boolean | null;
  };
};

// 地図コンポーネント本体
export default function ToiletMap({ filters }: ToiletMapProps) {
  const [toilets, setToilets] = useState<Toilet[]>([]);
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);

  // Google Maps APIの読み込み
  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
    language: "ja",
  });

  // フィルターが変更されたらAPIからデータを再取得
  useEffect(() => {
    const fetchToilets = async () => {
      const params = new URLSearchParams();
      if (filters.wheelchair) params.append("wheelchair", "true");
      if (filters.diaper) params.append("diaper", "true");
      if (filters.ostomate) params.append("ostomate", "true");
      if (filters.inside_gate !== null) {
        params.append("inside_gate_filter", filters.inside_gate ? "true" : "false");
      }

      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${API_BASE_URL}/api/toilets?${params.toString()}`);
        if (!res.ok) {
          throw new Error("Failed to fetch toilets");
        }
        const data: Toilet[] = await res.json();
        setToilets(data);
      } catch (error) {
        console.error(error);
      }
    };

    fetchToilets();
  }, [filters]);

  // 地図のスタイル設定
  const containerStyle = {
    width: "100%",
    height: "100%",
  };

  // 初期表示の中心座標（例: 上野駅周辺）
  const center = {
    lat: 35.7138,
    lng: 139.777,
  };

  // 地図がクリックされたら吹き出しを閉じる
  const onMapClick = useCallback(() => {
    setSelectedToilet(null);
  }, []);

  return isLoaded ? (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={center}
      zoom={15}
      options={{
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        clickableIcons: false,
      }}
      onClick={onMapClick}
    >
      {/* トイレのピンを表示 */}
      {toilets.map((toilet) => (
        <MarkerF
          key={toilet.id}
          position={{ lat: toilet.latitude, lng: toilet.longitude }}
          onClick={() => setSelectedToilet(toilet)}
        />
      ))}

      {/* 選択されたトイレがある場合のみ吹き出しを表示 */}
      {selectedToilet && (
        <InfoWindowF
          position={{ lat: selectedToilet.latitude, lng: selectedToilet.longitude }}
          onCloseClick={() => setSelectedToilet(null)}
          options={{ pixelOffset: new google.maps.Size(0, -30) }}
        >
          {/* 吹き出しの中身 */}
          <div className="p-1 min-w-[220px] text-gray-800">
            <h3 className="font-bold text-base text-blue-700 mb-2">{selectedToilet.name}</h3>
            
            {/* 営業時間 */}
            {selectedToilet.opening_hours && (
               <p className="text-xs text-gray-600 mb-2">🕘 {selectedToilet.opening_hours}</p>
            )}

            {/* 設備情報リスト */}
            <div className="flex flex-col gap-1 text-sm bg-gray-50 p-2 rounded border">
               {/* 改札内/外 */}
               {selectedToilet.inside_gate !== null && (
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🚇</span>
                    <span className="font-semibold badge badge-neutral badge-sm text-white">
                      {selectedToilet.inside_gate ? '改札内' : '改札外'}
                    </span>
                  </div>
               )}
               {/* 車椅子 */}
               <div className={`flex items-center gap-2 ${selectedToilet.is_wheelchair_accessible ? "text-green-700 font-medium" : "text-gray-400"}`}>
                 <span className="text-lg">♿</span>
                 <span>車椅子: {selectedToilet.is_wheelchair_accessible ? '〇' : '×'}</span>
               </div>
               {/* おむつ交換台 */}
               <div className={`flex items-center gap-2 ${selectedToilet.has_diaper_changing_station ? "text-green-700 font-medium" : "text-gray-400"}`}>
                 <span className="text-lg">👶</span>
                 <span>おむつ台: {selectedToilet.has_diaper_changing_station ? '〇' : '×'}</span>
               </div>
               {/* オストメイト */}
               <div className={`flex items-center gap-2 ${selectedToilet.is_ostomate_accessible ? "text-green-700 font-medium" : "text-gray-400"}`}>
                 <span className="text-lg">✚</span>
                 <span>オストメイト: {selectedToilet.is_ostomate_accessible ? '〇' : '×'}</span>
               </div>
            </div>

            {/* Googleマップへのリンク (公式推奨フォーマット) */}
            <a
               href={`https://www.google.com/maps/dir/?api=1&destination=${selectedToilet.latitude},${selectedToilet.longitude}`}
               target="_blank"
               rel="noopener noreferrer"
               className="btn btn-primary btn-sm w-full mt-3 text-white no-underline flex items-center justify-center gap-1"
            >
              <span>🗺️</span> ルート案内
            </a>
          </div>
        </InfoWindowF>
      )}
    </GoogleMap>
    
  ) : (
    <div className="w-full h-full flex items-center justify-center bg-gray-100">
      <p className="text-gray-500 animate-pulse">地図を読み込み中...</p>
    </div>
  );
}