"use client";
import { GoogleMap, useJsApiLoader, MarkerF } from "@react-google-maps/api";
import { useEffect, useState } from "react";

// (Toilet, ToiletMapProps の型定義は変更なし)
type Toilet = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  is_wheelchair_accessible: boolean;
  has_diaper_changing_station: boolean;
  is_ostomate_accessible: boolean;
  inside_gate: boolean;
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

  // ★★★ 修正箇所 ★★★
  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
    language: "ja", // ← この1行を追加
  });
  // ★★★ ここまで ★★★

  useEffect(() => {
    // フィルターが変更されたらAPIを叩き直す
    const fetchToilets = async () => {
      // フィルター条件をクエリパラメータに変換
      const params = new URLSearchParams();
      if (filters.wheelchair) {
        params.append("wheelchair", "true");
      }
      if (filters.diaper) {
        params.append("diaper", "true");
      }
      if (filters.ostomate) {
        params.append("ostomate", "true");
      }
      if (filters.inside_gate !== null) {
        params.append("inside_gate_filter", filters.inside_gate ? "true" : "false");
      }

      try {
        // Next.jsのプロキシ経由でFastAPI(/api/toilets)を呼び出す
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
  }, [filters]); // filters オブジェクトが変更されるたびに実行

  // ... (containerStyle, center は変更なし)
  const containerStyle = {
    width: "100%",
    height: "100%",
  };

  const center = {
    lat: 35.7138, // 上野駅周辺
    lng: 139.777,
  };

  return isLoaded ? (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={center}
      zoom={14}
      options={{
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false, // フルスクリーンボタンも非表示
      }}
    >
      {toilets.map((toilet) => (
        <MarkerF
          key={toilet.id}
          position={{ lat: toilet.latitude, lng: toilet.longitude }}
          onClick={() => {
            // マーカークリック時の動作（将来的に情報ウィンドウなどを表示）
            console.log(toilet.name);
          }}
        />
      ))}
    </GoogleMap>
  ) : (
    // ロード中に表示する内容
    <div className="flex h-full w-full items-center justify-center">
      <p>地図を読み込んでいます...</p>
    </div>
  );
}