'use client';

import React from 'react';
import { Clock, Train, ArrowRight, MapPin } from 'lucide-react';
import { StationToilet } from '@/types'; // 更新した型を読み込み

type Props = {
  options: StationToilet[];
  onSelect: (toilet: StationToilet) => void;
};

export function DecisionScreen({ options, onSelect }: Props) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-800 px-1">
        最適解が見つかりました
      </h2>
      
      <div className="space-y-4">
        {options.map((option) => (
          <div 
            key={option.id}
            onClick={() => onSelect(option)}
            className="bg-white rounded-2xl p-5 shadow-lg border-2 border-transparent hover:border-blue-500 transition-all active:scale-95 cursor-pointer relative overflow-hidden group"
          >
            {/* ★ここがキモ: 推奨号車があればデカデカと表示！ */}
            {option.bestCar && (
              <div className="absolute top-0 right-0 bg-gradient-to-bl from-red-500 to-pink-600 text-white px-4 py-2 rounded-bl-2xl shadow-md z-10">
                <div className="flex flex-col items-center leading-tight">
                  <span className="text-[10px] opacity-90 font-bold">乗るべき</span>
                  <span className="text-xl font-black tracking-tighter">{option.bestCar}</span>
                </div>
              </div>
            )}

            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  {option.name}
                </h3>
                <p className="text-sm text-gray-500 font-medium flex items-center gap-1 mt-1">
                   <MapPin className="w-3 h-3" />
                   {option.stationName || '詳細不明'}
                </p>
              </div>
            </div>

            {/* 戦略情報の表示エリア */}
            <div className="bg-blue-50 rounded-xl p-3 mt-3 space-y-2">
              {/* 施設情報（階段・エスカレーター） */}
              {option.platformInfo ? (
                <div className="flex items-center gap-2 text-blue-800 font-bold text-sm">
                  <Train className="w-4 h-4" />
                  <span>{option.platformInfo}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-gray-400 text-xs">
                  <Train className="w-4 h-4" />
                  <span>車両情報なし</span>
                </div>
              )}

              {/* 所要時間 */}
              <div className="flex items-center gap-2 text-gray-600 text-xs border-t border-blue-100 pt-2">
                <Clock className="w-3 h-3" />
                <span>ホームから約 {option.timeToToilet || '??分'}</span>
                {option.tags.includes('改札内') && (
                  <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-[10px] font-bold ml-auto">
                    改札内
                  </span>
                )}
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <span className="text-blue-600 text-sm font-bold flex items-center group-hover:translate-x-1 transition-transform">
                ここに行く <ArrowRight className="w-4 h-4 ml-1" />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}