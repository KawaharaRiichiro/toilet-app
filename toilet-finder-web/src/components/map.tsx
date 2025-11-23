"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF } from '@react-google-maps/api';

// --- 設定 ---
const containerStyle = {
  width: '100%',
  height: '100vh'
};

// 初期表示位置 (東京駅周辺)
const defaultCenter = {
  lat: 35.681236,
  lng: 139.767125
};

// --- 型定義 ---
interface Toilet {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
  is_station_toilet: boolean;
  opening_hours?: string;
  availability_notes?: string;
  is_wheelchair_accessible?: boolean;
  has_diaper_changing_station?: boolean;
  is_ostomate_accessible?: boolean;
}

export default function Map() {
  // 1. Google Maps APIのロード
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    // .env.local に NEXT_PUBLIC_GOOGLE_MAPS_API_KEY を設定してください
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "" 
  });

  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [toilets, setToilets] = useState<Toilet[]>([]);
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);
  const [center, setCenter] = useState(defaultCenter);

  // 2. APIからトイレデータを取得する関数
  const fetchToilets = async (lat: number, lng: number) => {
    try {
      // バックエンドの正しいエンドポイント (/toilets/nearby) を呼び出す
      const res = await fetch(`http://127.0.0.1:8000/toilets/nearby?lat=${lat}&lng=${lng}`);
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      setToilets(data);
    } catch (error) {
      console.error("トイレデータの取得に失敗:", error);
    }
  };

  // 3. マップがロードされた時の処理
  const onLoad = useCallback(function callback(map: google.maps.Map) {
    setMap(map);
    // 現在地を取得して移動
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const newCenter = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude
          };
          setCenter(newCenter);
          map.panTo(newCenter);
          fetchToilets(newCenter.lat, newCenter.lng);
        },
        () => {
          // 現在地が取れない場合は初期位置で検索
          fetchToilets(defaultCenter.lat, defaultCenter.lng);
        }
      );
    } else {
      fetchToilets(defaultCenter.lat, defaultCenter.lng);
    }
  }, []);

  const onUnmount = useCallback(function callback(map: google.maps.Map) {
    setMap(null);
  }, []);

  // 4. 地図が移動・ズーム終了した時のイベント (onIdle)
  const onIdle = () => {
    if (map) {
      const newCenter = map.getCenter();
      if (newCenter) {
        const lat = newCenter.lat();
        const lng = newCenter.lng();
        fetchToilets(lat, lng);
      }
    }
  };

  if (!isLoaded) return <div>Loading Map...</div>;

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={center}
      zoom={16}
      onLoad={onLoad}
      onUnmount={onUnmount}
      onIdle={onIdle} // 移動が終わったら再検索
      options={{
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
      }}
    >
      {toilets.map((toilet) => (
        <MarkerF
          key={toilet.id}
          position={{ lat: toilet.latitude, lng: toilet.longitude }}
          onClick={() => setSelectedToilet(toilet)}
          // アイコンの出し分け (Google標準アイコンを使用)
          icon={{
            url: toilet.is_station_toilet
              ? "http://maps.google.com/mapfiles/ms/icons/red-dot.png"  // 駅トイレ: 赤
              : "http://maps.google.com/mapfiles/ms/icons/blue-dot.png" // 公衆トイレ: 青
          }}
        />
      ))}

      {selectedToilet && (
        <InfoWindowF
          position={{ lat: selectedToilet.latitude, lng: selectedToilet.longitude }}
          onCloseClick={() => setSelectedToilet(null)}
        >
          <div style={{ minWidth: '200px', color: 'black' }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '5px', fontSize: '16px' }}>
              {selectedToilet.name}
            </h3>
            
            <div style={{ marginBottom: '8px' }}>
              <span style={{ 
                backgroundColor: selectedToilet.is_station_toilet ? '#ef4444' : '#3b82f6',
                color: 'white', 
                padding: '2px 6px', 
                borderRadius: '4px',
                fontSize: '12px' 
              }}>
                {selectedToilet.is_station_toilet ? '駅トイレ' : '公衆トイレ'}
              </span>
            </div>

            {selectedToilet.address && (
              <p style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                {selectedToilet.address}
              </p>
            )}

            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '5px' }}>
              {selectedToilet.is_wheelchair_accessible && <span style={tagStyle}>♿ 車椅子</span>}
              {selectedToilet.has_diaper_changing_station && <span style={tagStyle}>👶 ベビー</span>}
              {selectedToilet.is_ostomate_accessible && <span style={tagStyle}>✚ オストメイト</span>}
            </div>

            {selectedToilet.opening_hours && (
              <p style={{ fontSize: '12px', borderTop: '1px solid #eee', paddingTop: '4px' }}>
                🕒 {selectedToilet.opening_hours}
              </p>
            )}
          </div>
        </InfoWindowF>
      )}
    </GoogleMap>
  );
}

const tagStyle = {
  border: '1px solid #ccc',
  borderRadius: '4px',
  padding: '1px 4px',
  fontSize: '10px',
  backgroundColor: '#f3f4f6'
};