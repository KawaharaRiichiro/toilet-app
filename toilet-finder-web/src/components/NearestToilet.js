"use client";

import { useState, useEffect, useRef, useMemo } from 'react';
import { GoogleMap, useLoadScript, Marker, InfoWindow } from '@react-google-maps/api';

const libraries = ['places', 'geometry'];

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
  const [toilets, setToilets] = useState([]);
  const [selectedToilet, setSelectedToilet] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  
  const mapRef = useRef(null);
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { isLoaded } = useLoadScript({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY,
    libraries,
  });

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
        if (mapRef.current) mapRef.current.panTo(pos);
      },
      (err) => console.error(err)
    );
  }, []);

  // 2. データ取得
  useEffect(() => {
    async function fetchToilets() {
      if (!userLocation) return;
      
      try {
        const res = await fetch(`${API_BASE_URL}/api/nearest?lat=${userLocation.lat}&lng=${userLocation.lng}&limit=2000`);
        if (!res.ok) throw new Error('Failed to fetch nearest toilets');
        const data = await res.json();

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

        // 重複除去（公衆優先）
        const publicToilets = filtered.filter(t => !t.is_station_toilet);
        const stationToilets = filtered.filter(t => t.is_station_toilet);
        const uniqueStationToilets = stationToilets.filter(st => {
          const hasDuplicate = publicToilets.some(pt => {
            const dist = calculateDistance(st.latitude, st.longitude, pt.latitude, pt.longitude);
            return dist < 30; 
          });
          return !hasDuplicate;
        });
        
        const combined = [...publicToilets, ...uniqueStationToilets];
        const withDistance = combined.map(t => ({
          ...t,
          distance: calculateDistance(userLocation.lat, userLocation.lng, t.latitude, t.longitude)
        }));

        withDistance.sort((a, b) => (a.distance || 0) - (b.distance || 0));

        setToilets(withDistance);

        if (onUpdateNearest) {
          onUpdateNearest(withDistance.length > 0 ? withDistance[0] : null);
        }

      } catch (err) {
        console.error("API Error:", err);
      }
    }
    fetchToilets();
  }, [userLocation, filters, API_BASE_URL, onUpdateNearest]);

  if (!isLoaded) return <div className="p-4 text-center">地図読み込み中...</div>;

  return (
    <div className="h-full w-full relative">
       <GoogleMap
          zoom={16}
          center={{ lat: 35.681236, lng: 139.767125 }} 
          mapContainerStyle={{ width: '100%', height: '100%' }}
          options={{ streetViewControl: false, mapTypeControl: false, fullscreenControl: false }}
          onLoad={map => {
            mapRef.current = map;
            if(userLocation) map.panTo(userLocation);
          }}
        >
          {userLocation && (
            <Marker
              position={userLocation}
              icon={{
                path: google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: "#4285F4", // 現在地（青）
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
              // ★修正: SVGパスで色分け
              icon={{
                  path: google.maps.SymbolPath.CIRCLE,
                  scale: 7,
                  fillColor: toilet.is_station_toilet ? "#9333ea" : "#ef4444", // 紫(駅) / 赤(公衆)
                  fillOpacity: 1,
                  strokeColor: "white",
                  strokeWeight: 2,
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