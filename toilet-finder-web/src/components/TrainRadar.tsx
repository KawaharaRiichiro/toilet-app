import React from 'react';
import { motion } from 'framer-motion';

type Props = {
  userCar: number;
  targetCar: number;
  totalCars?: number;
};

export const TrainRadar: React.FC<Props> = ({ userCar, targetCar, totalCars = 10 }) => {
  const cars = Array.from({ length: totalCars }, (_, i) => i + 1);

  // 距離計算
  const distance = Math.abs(userCar - targetCar);
  const isFar = distance > 2; // 2両以上離れていたら「遠い」判定
  const isZero = distance === 0;

  // 線の座標計算 (各車両の中心から中心へ)
  // 車両幅は約10%と仮定し、中心点(5%)を基準にする
  const startCar = Math.min(userCar, targetCar);
  const leftPos = (startCar - 1) * 10 + 5; // 左端からの位置(%)
  const widthVal = distance * 10;          // 線の長さ(%)

  return (
    <div className="w-full mt-5 mb-2 px-1">
      <div className="flex justify-between items-center gap-1 relative">
        
        {/* 接続ライン (Z-indexを5に上げ、グレーの箱より手前に表示) */}
        {!isZero && (
          <div 
            className={`absolute h-1 top-1/2 -translate-y-1/2 rounded-full transition-all duration-500 z-[5]
              ${isFar ? 'bg-red-400 opacity-80' : 'bg-green-400 opacity-80'}
            `}
            style={{
              left: `${leftPos}%`,
              width: `${widthVal}%`
            }}
          >
             {/* 簡易的な矢印の先端 (CSSで表現) */}
             <div className={`absolute -right-1 -top-1 w-3 h-3 border-t-2 border-r-2 transform rotate-45 
               ${isFar ? 'border-red-400' : 'border-green-400'}
             `} />
          </div>
        )}

        {/* 各車両の描画 */}
        {cars.map((carNum) => {
          const isUser = carNum === userCar;
          const isTarget = carNum === targetCar;
          
          let bgColor = 'bg-gray-100';
          let scale = 1;

          if (isUser) {
            bgColor = 'bg-blue-600'; 
            scale = 1.1;
          } else if (isTarget) {
            bgColor = isFar ? 'bg-red-500' : 'bg-green-500';
            scale = 1.1;
          }

          return (
            <motion.div
              key={carNum}
              initial={{ scale: 0 }}
              animate={{ scale: scale }}
              // z-index: アクティブな車両は10、それ以外は0
              className={`
                relative flex-1 h-8 rounded-md flex items-center justify-center text-[10px] font-bold border border-transparent
                ${bgColor} 
                ${isUser || isTarget ? 'text-white shadow-md z-10' : 'text-gray-300 z-0'}
              `}
            >
              {carNum}

              {/* マーカー: YOU */}
              {isUser && (
                <div className="absolute -top-4 text-[9px] text-blue-600 font-black tracking-tighter">YOU</div>
              )}
              
              {/* マーカー: GOAL (遠い時は赤、近い時は緑) */}
              {isTarget && (
                <div className={`absolute -bottom-5 text-[9px] font-black tracking-tighter whitespace-nowrap ${isFar ? 'text-red-500' : 'text-green-500'}`}>
                  {isFar ? 'GOAL' : 'GOAL'}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};