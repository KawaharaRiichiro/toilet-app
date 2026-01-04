// src/types/index.ts

export type StationToilet = {
  id: string;
  name: string;
  lat: number;
  lng: number;
  stationName?: string;
  tags: string[];
  
  // ★変更: IBS戦略用の新項目 (APIのレスポンスに合わせる)
  bestCar?: string;       // 例: "7号車"
  platformInfo?: string;  // 例: "階段が近いです"
  timeToToilet?: string;  // 例: "3分"
  notes?: string;         // 例: "南口改札..."
};