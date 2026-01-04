'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import Map, { Marker, Popup, NavigationControl, GeolocateControl, MapRef } from 'react-map-gl';
import useSupercluster from 'use-supercluster';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MapPin, Navigation, Loader2 } from 'lucide-react';

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

export default function MapComponent({ targetLocation }: MapProps) {
  const mapRef = useRef<MapRef>(null);
  const [viewState, setViewState] = useState({
    latitude: 35.681236, // 東京駅
    longitude: 139.767125,
    zoom: 13
  });
  const [points, setPoints] = useState<any[]>([]);
  const [selectedToilet, setSelectedToilet] = useState<Toilet | null>(null);
  const [loading, setLoading] = useState(false);

  const onMapLoad = useCallback((e: any) => {
    const map = e.target;
    if (map) {
       try {
         const language = new MapboxLanguage({ defaultLanguage: 'ja' });
         map.addControl(language);
       } catch (error) {
         console.error("MapboxLanguage init failed:", error);
       }
    }
  }, []);

  useEffect(() => {
    if (targetLocation) {
      setViewState(prev => ({
        ...prev,
        latitude: targetLocation.lat,
        longitude: targetLocation.lng,
        zoom: targetLocation.zoom || 15,
      }));
      mapRef.current?.flyTo({
        center: [targetLocation.lng, targetLocation.lat],
        zoom: targetLocation.zoom || 15,
        duration: 1000
      });
    }
  }, [targetLocation]);

  useEffect(() => {
    const fetchPoints = async () => {
      setLoading(true);
      try {
        // 本番環境ではAPIから取得する想定（現在はモック）
        const mockPoints = Array.from({ length: 50 }).map((_, i) => ({
          type: 'Feature',
          properties: {
            cluster: false,
            toiletId: `t-${i}`,
            name: `トイレ ${i+1}`,
            category: Math.random() > 0.5 ? 'station' : 'public'
          },
          geometry: {
            type: 'Point',
            coordinates: [
              139.767125 + (Math.random() - 0.5) * 0.1,
              35.681236 + (Math.random() - 0.5) * 0.1
            ]
          }
        }));
        
        setPoints(mockPoints);
      } catch (error) {
        console.error("Failed to fetch toilets:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPoints();
  }, []);

  const bounds = mapRef.current
    ? (mapRef.current.getMap()?.getBounds()?.toArray().flat() as [number, number, number, number] | undefined)
    : undefined;

  const { clusters, supercluster } = useSupercluster({
    points,
    bounds,
    zoom: viewState.zoom,
    options: { radius: 75, maxZoom: 20 }
  });

  return (
    <div className="w-full h-full relative rounded-xl overflow-hidden shadow-inner border border-gray-200">
      {loading && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-white/50 backdrop-blur-sm">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      )}

      <Map
        {...viewState}
        ref={mapRef}
        onMove={evt => setViewState(evt.viewState)}
        onLoad={onMapLoad}
        style={{ width: '100%', height: '100%' }}
        mapStyle="mapbox://styles/mapbox/streets-v12"
        mapboxAccessToken={MAPBOX_TOKEN}
        maxZoom={20}
        minZoom={5}
      >
        <NavigationControl position="bottom-right" />
        <GeolocateControl position="top-right" trackUserLocation />

        {clusters.map((cluster) => {
          const [longitude, latitude] = cluster.geometry.coordinates;
          const { cluster: isCluster, point_count: pointCount } = cluster.properties;

          if (isCluster) {
            return (
              <Marker
                key={`cluster-${cluster.id}`}
                longitude={longitude}
                latitude={latitude}
                onClick={() => {
                  const clusterId = cluster.id;
                  
                  // ★修正: 型エラー回避のため、clusterIdが数値であることを確認
                  if (!supercluster || typeof clusterId !== 'number') {
                    return;
                  }

                  const expansionZoom = Math.min(
                    supercluster.getClusterExpansionZoom(clusterId),
                    20
                  );

                  setViewState({
                    ...viewState,
                    latitude,
                    longitude,
                    zoom: expansionZoom,
                  });
                  mapRef.current?.flyTo({
                    center: [longitude, latitude],
                    zoom: expansionZoom,
                    duration: 500
                  });
                }}
              >
                <div
                  className="rounded-full bg-blue-500 text-white flex items-center justify-center border-2 border-white shadow-md cursor-pointer hover:bg-blue-600 transition-colors"
                  style={{
                    width: `${30 + (pointCount / points.length) * 20}px`,
                    height: `${30 + (pointCount / points.length) * 20}px`,
                    fontSize: '12px',
                    fontWeight: 'bold'
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
                setSelectedToilet({
                  id: cluster.properties.toiletId,
                  name: cluster.properties.name,
                  lat: latitude,
                  lng: longitude,
                  details: { stationName: cluster.properties.category === 'station' ? '駅トイレ' : undefined }
                });
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
  );
}