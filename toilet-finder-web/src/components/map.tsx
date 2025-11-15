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
  address: string;
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

export default function ToiletMap({ filters }: ToiletMapProps) {
  const [toilets, setToilets] = useState<Toilet[]>([]);
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);
  const supabase = createClientComponentClient();

  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
    language: "ja",
    libraries: libraries,
  });

  // フィルタリング
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
      // Supabaseから全件取得
      const { data, error } = await supabase
        .from("toilets")
        .select("*")
        .limit(5000);

      if (!error && data) {
        setToilets(data as Toilet[]);
      }
    };
    fetchToilets();
  }, [supabase]);

  const onLoad = useCallback(function callback(map: google.maps.Map) {
    const bounds = new google.maps.LatLngBounds();
    bounds.extend({ lat: 35.681236, lng: 139.767125 });
    map.fitBounds(bounds);
    const listener = google.maps.event.addListener(map, "idle", () => { 
      if (map.getZoom()! > 15) map.setZoom(15); 
      google.maps.event.removeListener(listener); 
    });
  }, []);

  if (!isLoaded) return <div className="w-full h-full flex items-center justify-center">地図を読み込み中...</div>;

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={{ lat: 35.681236, lng: 139.767125 }}
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
          // 駅トイレは紫
          icon={toilet.is_station_toilet ? "http://maps.google.com/mapfiles/ms/icons/purple-dot.png" : undefined}
        />
      ))}

      {selectedToilet && (
        <InfoWindowF
          position={{ lat: selectedToilet.latitude, lng: selectedToilet.longitude }}
          onCloseClick={() => setSelectedToilet(null)}
        >
          <div className="p-2 min-w-[200px] text-black">
            <h3 className="font-bold text-lg mb-1 flex items-center">
              {selectedToilet.is_station_toilet && <span className="mr-1 text-lg">🚉</span>}
              {selectedToilet.name}
            </h3>
            <p className="text-sm text-gray-600 mb-2">{selectedToilet.address}</p>
            
            <div className="flex flex-wrap gap-1 mb-2">
               {selectedToilet.is_wheelchair_accessible && <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">♿</span>}
               {selectedToilet.has_diaper_changing_station && <span className="text-xs bg-pink-100 text-pink-800 px-1 rounded">👶</span>}
               {selectedToilet.is_ostomate_accessible && <span className="text-xs bg-green-100 text-green-800 px-1 rounded">✚</span>}
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