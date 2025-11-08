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
  opening_hours: string | null;         // 追加: 営業時間
  availability_notes: string | null;    // 追加: 利用可能時間などのメモ
  is_wheelchair_accessible: boolean;
  has_diaper_changing_station: boolean;
  is_ostomate_accessible: boolean;
  inside_gate: boolean;
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
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null); // ★追加: 選択されたトイレ

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
  // ※ 実際のアプリでは、ユーザーの現在地を初期値にするのがベターです
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
      zoom={15} // 少しズームアップ
      options={{
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        clickableIcons: false, // 地図上の他のアイコンをクリック不可に
      }}
      onClick={onMapClick} // 地図クリックで選択解除
    >
      {/* トイレのピンを表示 */}
      {toilets.map((toilet) => (
        <MarkerF
          key={toilet.id}
          position={{ lat: toilet.latitude, lng: toilet.longitude }}
          onClick={() => setSelectedToilet(toilet)} // ★追加: クリックで選択
          // フィルタ条件に応じてピンの色を変えるなどの工夫も可能
          // icon={{ url: "..." }} 
        />
      ))}

      {/* ★追加: 選択されたトイレがある場合のみ吹き出しを表示 */}
      {selectedToilet && (
        <InfoWindowF
          position={{ lat: selectedToilet.latitude, lng: selectedToilet.longitude }}
          onCloseClick={() => setSelectedToilet(null)} // ✕ボタンで閉じる
          options={{ pixelOffset: new google.maps.Size(0, -30) }} // ピンの上に表示
        >
          {/* 吹き出しの中身（HTML/Tailwind CSSで自由にデザイン可能） */}
          <div className="p-2 max-w-xs">
            <h3 className="font-bold text-lg text-blue-700 mb-1">{selectedToilet.name}</h3>
            
            {/* 営業時間などがあれば表示 */}
            {selectedToilet.opening_hours && (
               <p className="text-sm text-gray-600 mb-2">🕘 {selectedToilet.opening_hours}</p>
            )}

            {/* 設備バッジ */}
            <div className="flex flex-wrap gap-1 mb-2">
              {selectedToilet.inside_gate && (
                <span className="badge badge-sm badge-neutral text-white">改札内</span>
              )}
              {selectedToilet.is_wheelchair_accessible && (
                <span className="badge badge-sm badge-success text-white">車椅子OK</span>
              )}
               {selectedToilet.has_diaper_changing_station && (
                <span className="badge badge-sm badge-info text-white">おむつ台</span>
              )}
               {selectedToilet.is_ostomate_accessible && (
                <span className="badge badge-sm badge-warning text-white">オストメイト</span>
              )}
            </div>

            {/* Googleマップへのリンク */}
            <a
               href={`https://www.google.com/maps/dir/?api=1&destination=${selectedToilet.latitude},${selectedToilet.longitude}`}
               target="_blank"
               rel="noopener noreferrer"
               className="btn btn-primary btn-xs w-full mt-2"
            >
              ここへ行く 🏃‍♂️
            </a>
          </div>
        </InfoWindowF>
      )}
    </GoogleMap>
  ) : (
    // ロード中の表示
    <div className="w-full h-full flex items-center justify-center bg-gray-100">
      <p className="text-gray-500">地図を読み込み中...</p>
    </div>
  );
}