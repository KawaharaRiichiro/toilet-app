"use client";

import { useState, useEffect, useRef, useMemo } from 'react';
import { GoogleMap, useLoadScript, Marker, InfoWindow } from '@react-google-maps/api';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

const libraries = ['places', 'geometry'];

// 距離計算（親コンポーネントで表示するため）
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  if (!lat1 || !lon1 || !lat2 || !lon2) return null;
  const R = 6371e3; 
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ/2) * Math.sin(Δλ/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

export default function NearestToilet({ filters, onUpdateNearest }) {
  const [toilets, setToilets] = useState([]); // マップ上の全ピン
  const [selectedToilet, setSelectedToilet] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  
  const mapRef = useRef(null);
  const supabase = createClientComponentClient();

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY,
    libraries,
  });

  // ★修正: 地図の初期位置をuseMemoで固定化（リセット防止）
  const defaultCenter = useMemo(() => ({ lat: 35.681236, lng: 139.767125 }), []);

  // 1. 現在地取得
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        setUserLocation(pos);
        // 地図がロード済みなら移動
        if (mapRef.current) {
          mapRef.current.panTo(pos);
        }
      },
      (err) => console.error(err)
    );
  }, []);

  // 2. データ取得 (Supabase RPCを直接呼ぶ)
  useEffect(() => {
    async function fetchToilets() {
      if (!userLocation) return;
      
      try {
        const { data, error } = await supabase
          .rpc('nearby_toilets', { 
            lat: userLocation.lat, 
            long: userLocation.lng 
          });

        if (!error && data) {
          // フィルタリング
          const filtered = data.filter(t => {
            if (filters?.wheelchair && !t.is_wheelchair_accessible) return false;
            if (filters?.diaper && !t.has_diaper_changing_station) return false;
            if (filters?.ostomate && !t.is_ostomate_accessible) return false;
            if (filters?.inside_gate !== null && filters?.inside_gate !== undefined) {
               if (t.inside_gate !== filters.inside_gate) return false;
            }
            return true;
          });

          // 距離を計算して付与
          const withDistance = filtered.map(t => ({
            ...t,
            distance: calculateDistance(userLocation.lat, userLocation.lng, t.latitude, t.longitude)
          }));

          setToilets(withDistance); // マップのピン用

          // 親(page.tsx)に一番近いトイレ情報を渡す
          if (onUpdateNearest) {
            onUpdateNearest(withDistance.length > 0 ? withDistance[0] : null);
          }
        }
      } catch (err) {
        console.error(err);
      }
    }
    fetchToilets();
  }, [userLocation, filters, supabase, onUpdateNearest]);

  if (loadError) return <div className="p-4 text-center">地図の読み込みに失敗しました</div>;
  if (!isLoaded) return <div className="p-4 text-center">地図を読み込み中...</div>;

  return (
    <div className="h-full w-full relative">
       <GoogleMap
          zoom={16}
          center={defaultCenter} // 固定化した初期値を渡す
          mapContainerStyle={{ width: '100%', height: '100%' }}
          options={{ streetViewControl: false, mapTypeControl: false, fullscreenControl: false }}
          onLoad={map => {
            mapRef.current = map;
            // ロード完了時に現在地（取得済みなら）へ移動
            if(userLocation) map.panTo(userLocation);
          }}
        >
          {userLocation && (
            <Marker
              position={userLocation}
              icon={{
                path: google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: "#4285F4",
                fillOpacity: 1,
                strokeColor: "white",
                strokeWeight: 2,
              }}
            />
          )}
          
          {toilets.map((toilet) => (
            <Marker
              key={toilet.id}
              position={{ lat: toilet.latitude, lng: toilet.longitude }}
              onClick={() => {
                  setSelectedToilet(toilet);
                  if (onUpdateNearest) onUpdateNearest(toilet);
              }}
              // 駅トイレは紫、それ以外は赤
              icon={{
                  url: toilet.is_station_toilet 
                  ? "http://maps.google.com/mapfiles/ms/icons/purple-dot.png" 
                  : "http://maps.google.com/mapfiles/ms/icons/red-dot.png" 
              }}
            />
          ))}

          {selectedToilet && (
              <InfoWindow
                  position={{ lat: selectedToilet.latitude, lng: selectedToilet.longitude }}
                  onCloseClick={() => setSelectedToilet(null)}
              >
                  <div className="p-1 text-black min-w-[120px]">
                      <strong>{selectedToilet.name}</strong>
                  </div>
              </InfoWindow>
          )}
       </GoogleMap>
    </div>
  );
}