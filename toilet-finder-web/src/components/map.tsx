"use client";

import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF } from "@react-google-maps/api";
import { useEffect, useState, useCallback, useMemo } from "react";

const libraries: ("places" | "geometry")[] = ["places", "geometry"];

const mapContainerStyle = {
  width: '100%',
  height: '100%',
};

type Toilet = {
  id: string;
  name: string;
  address: string | null;
  latitude: number;
  longitude: number;
  is_station_toilet: boolean;
  opening_hours: string | null;
  availability_notes: string | null;
  is_wheelchair_accessible: boolean;
  has_diaper_changing_station: boolean;
  is_ostomate_accessible: boolean;
  inside_gate: boolean | null;
  is_station_toilet: boolean;
};

type ToiletMapProps = {
  filters: {
    wheelchair: boolean;
    diaper: boolean;
    ostomate: boolean;
    inside_gate: boolean | null;
  };
};

export default function ToiletMap({ filters }: ToiletMapProps) {
  const [toilets, setToilets] = useState<Toilet[]>([]);
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);

  // API URL
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { isLoaded, loadError } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
    language: "ja",
    libraries: libraries,
  });

  const defaultCenter = useMemo(() => ({ lat: 35.681236, lng: 139.767125 }), []);

  // フィルタリング処理
  const filteredToilets = useMemo(() => {
    return toilets.filter((t) => {
      if (filters?.wheelchair && !t.is_wheelchair_accessible) return false;
      if (filters?.diaper && !t.has_diaper_changing_station) return false;
      if (filters?.ostomate && !t.is_ostomate_accessible) return false;
      if (filters?.inside_gate !== null && filters?.inside_gate !== undefined) {
         if (t.inside_gate !== filters.inside_gate) return false;
      }
      return true;
    });
  }, [toilets, filters]);

  useEffect(() => {
    const fetchToilets = async () => {
      try {
        // ★修正: limit=5000 を明示的に指定
        const res = await fetch(`${API_BASE_URL}/api/toilets?limit=5000`);
        if (!res.ok) throw new Error('Failed to fetch toilets');
        const data = await res.json();
        console.log(`✅ [Map] 取得件数: ${data.length} 件`);
        setToilets(data);
      } catch (error) {
        console.error("トイレデータの取得に失敗:", error);
      }
    };
    fetchToilets();
  }, [API_BASE_URL]);

  const onLoad = useCallback(function callback(map: google.maps.Map) {
    const bounds = new google.maps.LatLngBounds();
    bounds.extend(defaultCenter);
    map.setCenter(defaultCenter);
  }, [defaultCenter]);

  if (loadError) return <div className="h-full flex items-center justify-center text-red-500">地図エラー</div>;
  if (!isLoaded) return <div className="h-full flex items-center justify-center text-gray-500">読み込み中...</div>;

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={defaultCenter}
      zoom={15}
      onLoad={onLoad}
      options={{
        streetViewControl: false,
        mapTypeControl: false,
        fullscreenControl: false,
      }}
    >
      {filteredToilets.map((toilet) => (
        <MarkerF
          key={toilet.id}
          position={{ lat: toilet.latitude, lng: toilet.longitude }}
          onClick={() => setSelectedToilet(toilet)}
          icon={
            toilet.is_station_toilet
              ? "http://googleusercontent.com/maps.google.com/mapfiles/ms/icons/purple-dot.png" // 紫ピン
              : undefined
          }
        />
      ))}

      {selectedToilet && (
        <InfoWindowF
          position={{ lat: selectedToilet.latitude, lng: selectedToilet.longitude }}
          onCloseClick={() => setSelectedToilet(null)}
        >
          <div className="p-2 min-w-[150px] text-black">
            <h3 className="font-bold text-base mb-1 flex items-center">
              {selectedToilet.is_station_toilet && <span className="mr-1 text-lg">🚉</span>}
              {selectedToilet.name}
            </h3>
            <p className="text-xs text-gray-600 mb-2">{selectedToilet.address}</p>
            
            <div className="flex gap-1 flex-wrap mb-2">
               {selectedToilet.is_wheelchair_accessible && <span className="text-[10px] bg-blue-100 text-blue-800 px-1 rounded">♿</span>}
               {selectedToilet.has_diaper_changing_station && <span className="text-[10px] bg-pink-100 text-pink-800 px-1 rounded">👶</span>}
               {selectedToilet.is_ostomate_accessible && <span className="text-[10px] bg-green-100 text-green-800 px-1 rounded">✚</span>}
            </div>
            
            <a
               href={`https://www.google.com/maps/dir/?api=1&destination=${selectedToilet.latitude},${selectedToilet.longitude}`}
               target="_blank"
               rel="noopener noreferrer"
               className="btn btn-primary btn-sm w-full mt-2 text-white no-underline flex items-center justify-center"
            >
              ここへ行く
            </a>
          </div>
        </InfoWindowF>
      )}
    </GoogleMap>
  );
}