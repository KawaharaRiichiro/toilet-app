"use client";

import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF } from "@react-google-maps/api";
import { useEffect, useState, useCallback, useMemo } from "react";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";

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

// ★追加: 距離計算関数 (2点間のメートル数を返す)
const getDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
  const R = 6371e3; // 地球の半径(m)
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

export default function ToiletMap({ filters }: ToiletMapProps) {
  const [toilets, setToilets] = useState<Toilet[]>([]);
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);
  const supabase = createClientComponentClient();

  const defaultCenter = useMemo(() => ({ lat: 35.681236, lng: 139.767125 }), []);

  const { isLoaded, loadError } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
    language: "ja",
    libraries: libraries,
  });

  // ★修正: 重複除去とフィルタリングを同時に行う
  const displayToilets = useMemo(() => {
    // 1. まずフィルター条件で絞り込む
    const filtered = toilets.filter((t) => {
      if (filters?.wheelchair && !t.is_wheelchair_accessible) return false;
      if (filters?.diaper && !t.has_diaper_changing_station) return false;
      if (filters?.ostomate && !t.is_ostomate_accessible) return false;
      if (filters?.inside_gate !== null && filters?.inside_gate !== undefined) {
         if (t.inside_gate !== filters.inside_gate) return false;
      }
      return true;
    });

    // 2. 重複除去ロジック (ピンク優先)
    const publicToilets = filtered.filter(t => !t.is_station_toilet); // ピンク(公衆)
    const stationToilets = filtered.filter(t => t.is_station_toilet); // 紫(駅)

    const uniqueStationToilets = stationToilets.filter(st => {
      // この駅トイレの近く(30m以内)に公衆トイレがあるか？
      const hasDuplicate = publicToilets.some(pt => {
        const dist = getDistance(st.latitude, st.longitude, pt.latitude, pt.longitude);
        return dist < 30; // 30m以内なら重複とみなす
      });
      // 重複がなければ表示する
      return !hasDuplicate;
    });

    // 合体して返す
    return [...publicToilets, ...uniqueStationToilets];
  }, [toilets, filters]);

  useEffect(() => {
    async function fetchToilets() {
      // Supabaseから全件取得
      const { data, error } = await supabase
        .from("toilets")
        .select("*")
        .limit(5000);

      if (!error && data) {
        setToilets(data as Toilet[]);
      }
    }
    fetchToilets();
  }, [supabase]);

  const onLoad = useCallback(function callback(map: google.maps.Map) {
    const bounds = new google.maps.LatLngBounds();
    bounds.extend(defaultCenter);
    map.setCenter(defaultCenter);
  }, [defaultCenter]);

  if (loadError) return <div className="h-full flex items-center justify-center">地図エラー</div>;
  if (!isLoaded) return <div className="h-full flex items-center justify-center">読み込み中...</div>;

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
      {/* ★ displayToilets を使うように変更 */}
      {displayToilets.map((toilet) => (
        <MarkerF
          key={toilet.id}
          position={{ lat: toilet.latitude, lng: toilet.longitude }}
          onClick={() => setSelectedToilet(toilet)}
          icon={
            toilet.is_station_toilet
              ? "http://maps.google.com/mapfiles/ms/icons/purple-dot.png"
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
               href={`http://googleusercontent.com/maps.google.com/maps?q=${selectedToilet.latitude},${selectedToilet.longitude}`}
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