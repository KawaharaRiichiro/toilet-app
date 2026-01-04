'use client';

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import Map, { Source, Layer, Marker, Popup, NavigationControl, GeolocateControl, MapRef } from 'react-map-gl';
import useSupercluster from 'use-supercluster';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MapPin, Navigation, Loader2 } from 'lucide-react'; // Loader2を追加

// @ts-ignore
import MapboxLanguage from '@mapbox/mapbox-gl-language';

type Toilet = {
  id: string;
  name: string;
  lat: number;
  lng: number;
  details?: any;
};

type MapProps = {
  targetLocation?: {
    lat: number;
    lng: number;
    zoom?: number;
  } | null;
};

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const clusterLayer: any = {
  id: 'clusters',
  type: 'circle',
  source: 'toilets',
  filter: ['has', 'point_count'],
  paint: {
    'circle-color': ['step', ['get', 'point_count'], '#51bbd6', 10, '#f1f075', 50, '#f28cb1'],
    'circle-radius': ['step', ['get', 'point_count'], 20, 10, 30, 50, 40]
  }
};

const clusterCountLayer: any = {
  id: 'cluster-counts',
  type: 'symbol',
  source: 'toilets',
  filter: ['has', 'point_count'],
  layout: {
    'text-field': '{point_count_abbreviated}',
    'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
    'text-size': 12
  }
};

export default function MapComponent({ targetLocation }: MapProps) {
  const mapRef = useRef<MapRef>(null);

  const [toilets, setToilets] = useState<Toilet[]>([]);
  const [viewState, setViewState] = useState({
    latitude: 35.681236,
    longitude: 139.767125,
    zoom: 14
  });
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);

  // ★追加: 地図の準備完了状態を管理
  const [isReady, setIsReady] = useState(false);

  // 日本語化処理
  const onMapLoad = useCallback((evt: any) => {
    const map = evt.target;
    
    // プラグイン適用
    const language = new MapboxLanguage({ 
      defaultLanguage: 'ja' 
    });
    map.addControl(language);

    // 強制書き換え
    const style = map.getStyle();
    if (style && style.layers) {
      style.layers.forEach((layer: any) => {
        if (layer.type === 'symbol' && layer.layout && layer.layout['text-field']) {
          try {
            map.setLayoutProperty(layer.id, 'text-field', [
              'coalesce',
              ['get', 'name_ja'],
              ['get', 'name']
            ]);
          } catch (e) {
            // ignore
          }
        }
      });
    }

    // ★重要: 処理が終わったら「準備完了」とする（少しだけ待つとより滑らかです）
    setTimeout(() => {
      setIsReady(true);
    }, 200); 
  }, []);

  useEffect(() => {
    if (targetLocation && mapRef.current) {
      mapRef.current.flyTo({
        center: [targetLocation.lng, targetLocation.lat],
        zoom: targetLocation.zoom || 16,
        speed: 1.5,
        curve: 1,
        essential: true
      });
    }
  }, [targetLocation]);

  useEffect(() => {
    const fetchToilets = async () => {
      try {
        const url = `${API_BASE_URL}/toilets/nearby?lat=${viewState.latitude}&lng=${viewState.longitude}`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          const formatted = data.map((t: any) => ({
             id: t.id,
             name: t.stationName || t.name || 'トイレ',
             lat: t.lat || t.latitude,
             lng: t.lng || t.longitude,
             details: t
          }));
          setToilets(formatted);
        }
      } catch (err) {
        console.error("Failed to fetch toilets", err);
      }
    };

    const timer = setTimeout(fetchToilets, 500);
    return () => clearTimeout(timer);
  }, [viewState.latitude, viewState.longitude]);

  const points = useMemo(() => toilets.map(toilet => ({
    type: 'Feature' as const,
    properties: { cluster: false, toiletId: toilet.id, ...toilet },
    geometry: {
      type: 'Point' as const,
      coordinates: [toilet.lng, toilet.lat]
    }
  })), [toilets]);

  const bounds = mapRef.current
    ? mapRef.current.getMap().getBounds().toArray().flat() as [number, number, number, number]
    : undefined;

  const { clusters, supercluster } = useSupercluster({
    points,
    bounds,
    zoom: viewState.zoom,
    options: { radius: 75, maxZoom: 20 }
  });

  const onMove = useCallback((evt: any) => setViewState(evt.viewState), []);

  if (!MAPBOX_TOKEN) {
    return <div className="p-4 text-red-500">Mapbox Token Missing</div>;
  }

  return (
    <div className="w-full h-full relative bg-gray-100">
      
      {/* ★追加: ロード中のスピナー（地図が出るまで表示） */}
      {!isReady && (
        <div className="absolute inset-0 flex items-center justify-center z-10 bg-gray-50">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            <p className="text-xs text-gray-500 font-bold">MAP LOADING...</p>
          </div>
        </div>
      )}

      {/* 地図本体: 準備ができるまで opacity-0 で隠しておく */}
      <div 
        className={`w-full h-full transition-opacity duration-700 ease-in-out ${isReady ? 'opacity-100' : 'opacity-0'}`}
      >
        <Map
          {...viewState}
          ref={mapRef}
          onMove={onMove}
          onLoad={onMapLoad}
          mapStyle="mapbox://styles/mapbox/streets-v11"
          mapboxAccessToken={MAPBOX_TOKEN}
          style={{ width: '100%', height: '100%' }}
        >
          <NavigationControl position="top-right" />
          <GeolocateControl position="top-right" />

          <Source type="geojson" data={{ type: 'FeatureCollection', features: clusters }}>
            <Layer {...clusterLayer} />
            <Layer {...clusterCountLayer} />
          </Source>

          {clusters.map(cluster => {
            const [longitude, latitude] = cluster.geometry.coordinates;
            const { cluster: isCluster, point_count: pointCount } = cluster.properties;

            if (isCluster) {
              return (
                <Marker key={`cluster-${cluster.id}`} longitude={longitude} latitude={latitude}>
                  <div
                    className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-xs font-bold shadow-lg cursor-pointer hover:bg-blue-600 transition-colors"
                    onClick={() => {
                      const expansionZoom = Math.min(supercluster.getClusterExpansionZoom(cluster.id), 20);
                      mapRef.current?.flyTo({ center: [longitude, latitude], zoom: expansionZoom, speed: 1.2 });
                    }}
                  >
                    {pointCount}
                  </div>
                </Marker>
              );
            }

            return (
              <Marker
                key={`toilet-${cluster.properties.toiletId}`}
                longitude={longitude}
                latitude={latitude}
                anchor="bottom"
                onClick={(e) => {
                  e.originalEvent.stopPropagation();
                  setSelectedToilet(cluster.properties);
                }}
              >
                <MapPin className="text-blue-600 w-8 h-8 drop-shadow-md cursor-pointer hover:scale-110 transition-transform" />
              </Marker>
            );
          })}

          {targetLocation && (
            <Marker
              longitude={targetLocation.lng}
              latitude={targetLocation.lat}
              anchor="bottom"
            >
              <div className="flex flex-col items-center animate-bounce-slow">
                <div className="bg-red-600 text-white text-[10px] font-bold px-2 py-1 rounded shadow-md mb-1 whitespace-nowrap flex items-center gap-1">
                  <Navigation className="w-3 h-3" /> GOAL
                </div>
                <MapPin className="w-12 h-12 text-red-600 fill-white drop-shadow-xl stroke-[3px]" />
              </div>
            </Marker>
          )}

          {selectedToilet && (
            <Popup
              longitude={selectedToilet.lng}
              latitude={selectedToilet.lat}
              anchor="top"
              onClose={() => setSelectedToilet(null)}
              closeOnClick={false}
            >
              <div className="p-2 min-w-[150px]">
                <h3 className="font-bold text-gray-800 mb-1">{selectedToilet.name}</h3>
                <p className="text-xs text-gray-500">
                  {selectedToilet.details?.stationName ? '駅トイレ' : '公衆トイレ'}
                </p>
              </div>
            </Popup>
          )}
        </Map>
      </div>
    </div>
  );
}