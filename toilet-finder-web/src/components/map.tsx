"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF } from '@react-google-maps/api';

const containerStyle = {
  width: '100%',
  height: '100%'
};

const defaultCenter = {
  lat: 35.681236,
  lng: 139.767125
};

// 外部公開用の型定義（page.tsxでも使うため）
export interface Toilet {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
  is_station_toilet: boolean;
  is_wheelchair_accessible?: boolean;
  has_diaper_changing_station?: boolean;
  is_ostomate_accessible?: boolean;
  inside_gate?: boolean;
  distance?: number; // 距離情報を追加
}

// 親から受け取るプロパティ
interface MapProps {
  filters?: {
    wheelchair: boolean;
    diaper: boolean;
    ostomate: boolean;
    inside_gate: boolean | null;
  };
  // 最寄りトイレが見つかったら親に教える関数（任意）
  onUpdateNearest?: (toilet: Toilet | null) => void;
}

// 2点間の距離を計算する関数 (Haversine formula)
function getDistance(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371e3; // 地球の半径 (m)
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c; // 距離 (m)
}

export default function Map({ filters, onUpdateNearest }: MapProps) {
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "" 
  });

  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [toilets, setToilets] = useState<Toilet[]>([]);
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);
  const [center, setCenter] = useState(defaultCenter);
  const [currentPos, setCurrentPos] = useState<{lat: number, lng: number} | null>(null);

  // フィルタリング処理
  const filteredToilets = toilets.filter(t => {
    if (!filters) return true;
    if (filters.wheelchair && !t.is_wheelchair_accessible) return false;
    if (filters.diaper && !t.has_diaper_changing_station) return false;
    if (filters.ostomate && !t.is_ostomate_accessible) return false;
    if (filters.inside_gate !== null && t.inside_gate !== filters.inside_gate) return false;
    return true;
  });

  // APIからデータ取得 & 最寄り計算
  const fetchToilets = async (lat: number, lng: number) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/toilets/nearby?lat=${lat}&lng=${lng}`);
      if (!res.ok) throw new Error('API Error');
      const data: Toilet[] = await res.json();
      
      // 現在地との距離を計算してデータに追加
      const dataWithDistance = data.map(t => ({
        ...t,
        distance: getDistance(lat, lng, t.latitude, t.longitude)
      }));

      // 距離順にソート
      dataWithDistance.sort((a, b) => (a.distance || 0) - (b.distance || 0));

      setToilets(dataWithDistance);

      // 一番近いトイレを親コンポーネントに通知
      if (onUpdateNearest && dataWithDistance.length > 0) {
        onUpdateNearest(dataWithDistance[0]);
      } else if (onUpdateNearest) {
        onUpdateNearest(null);
      }

    } catch (error) {
      console.error("トイレデータの取得に失敗:", error);
    }
  };

  const onLoad = useCallback(function callback(map: google.maps.Map) {
    setMap(map);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const newCenter = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setCenter(newCenter);
          setCurrentPos(newCenter);
          map.panTo(newCenter);
          fetchToilets(newCenter.lat, newCenter.lng);
        },
        () => fetchToilets(defaultCenter.lat, defaultCenter.lng)
      );
    } else {
      fetchToilets(defaultCenter.lat, defaultCenter.lng);
    }
  }, []);

  const onUnmount = useCallback(function callback(map: google.maps.Map) {
    setMap(null);
  }, []);

  const onIdle = () => {
    if (map) {
      const newCenter = map.getCenter();
      if (newCenter) {
        const lat = newCenter.lat();
        const lng = newCenter.lng();
        // 現在地から大きく離れていないか確認（任意）
        // ここではドラッグするたびに再検索＆最寄り更新を行う
        fetchToilets(lat, lng);
      }
    }
  };

  if (!isLoaded) return <div className="w-full h-full flex items-center justify-center bg-gray-100">地図読み込み中...</div>;

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={center}
      zoom={16}
      onLoad={onLoad}
      onUnmount={onUnmount}
      onIdle={onIdle}
      options={{
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        zoomControl: false,
      }}
    >
      {/* 現在地マーカー (青い丸) */}
      {currentPos && (
        <MarkerF
          position={currentPos}
          icon={{
            path: google.maps.SymbolPath.CIRCLE,
            scale: 7,
            fillColor: "#4285F4",
            fillOpacity: 1,
            strokeColor: "white",
            strokeWeight: 2,
          }}
        />
      )}

      {filteredToilets.map((toilet) => (
        <MarkerF
          key={toilet.id}
          position={{ lat: toilet.latitude, lng: toilet.longitude }}
          onClick={() => setSelectedToilet(toilet)}
          icon={{
            url: toilet.is_station_toilet
              ? "http://maps.google.com/mapfiles/ms/icons/red-dot.png" 
              : "http://maps.google.com/mapfiles/ms/icons/blue-dot.png"
          }}
        />
      ))}

      {selectedToilet && (
        <InfoWindowF
          position={{ lat: selectedToilet.latitude, lng: selectedToilet.longitude }}
          onCloseClick={() => setSelectedToilet(null)}
        >
          <div style={{ color: 'black', minWidth: '180px' }}>
            <h3 style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>{selectedToilet.name}</h3>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
              {selectedToilet.is_station_toilet ? '🚉 駅トイレ' : '🚻 公衆トイレ'}
            </div>
            {selectedToilet.distance && (
              <div style={{ fontSize: '12px', color: '#ef4444', fontWeight: 'bold', marginBottom: '4px' }}>
                ここから約 {Math.round(selectedToilet.distance)}m
              </div>
            )}
            <div style={{ display: 'flex', gap: '2px' }}>
              {selectedToilet.is_wheelchair_accessible && <span>♿</span>}
              {selectedToilet.has_diaper_changing_station && <span>👶</span>}
              {selectedToilet.is_ostomate_accessible && <span>✚</span>}
            </div>
          </div>
        </InfoWindowF>
      )}
    </GoogleMap>
  );
}