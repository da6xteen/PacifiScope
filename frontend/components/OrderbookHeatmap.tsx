"use client";

import React, { useMemo } from 'react';
import { useStore } from '../lib/store';

const OrderbookHeatmap = () => {
  const history = useStore((state) => state.history);

  // Settings
  const TICK_COUNT = 60;
  const LEVEL_COUNT = 50; // ±25 levels
  const TICK_WIDTH = 12;
  const LEVEL_HEIGHT = 10;

  const width = TICK_COUNT * TICK_WIDTH;
  const height = LEVEL_COUNT * LEVEL_HEIGHT;

  const heatmapData = useMemo(() => {
    if (history.length === 0) return [];

    const latestSnapshot = history[history.length - 1];
    const bestBid = latestSnapshot.bids[0]?.[0] || 0;
    const bestAsk = latestSnapshot.asks[0]?.[0] || 0;
    const mid = (bestBid + bestAsk) / 2;

    const priceGap = Math.max(0.01, (latestSnapshot.asks[1]?.[0] || latestSnapshot.asks[0]?.[0] + 0.01) - latestSnapshot.asks[0]?.[0]);

    const dataToRender = history.slice(-TICK_COUNT);
    const rects: {
      x: number;
      y: number;
      width: number;
      height: number;
      fill: string;
      key: string;
    }[] = [];

    dataToRender.forEach((snapshot, tIndex) => {
      const x = (TICK_COUNT - 1 - (dataToRender.length - 1 - tIndex)) * TICK_WIDTH;

      // Bids
      snapshot.bids.forEach(([price, size]) => {
        const levelDiff = Math.round((mid - price) / priceGap);
        const yLevel = 25 + levelDiff;

        if (yLevel >= 0 && yLevel < LEVEL_COUNT) {
          const intensity = Math.min(1, Math.log10(size + 1) / 5);
          rects.push({
            x,
            y: yLevel * LEVEL_HEIGHT,
            width: TICK_WIDTH,
            height: LEVEL_HEIGHT,
            fill: `rgba(0, 255, 0, ${intensity})`,
            key: `bid-${tIndex}-${price}`
          });
        }
      });

      // Asks
      snapshot.asks.forEach(([price, size]) => {
        const levelDiff = Math.round((price - mid) / priceGap);
        const yLevel = 24 - levelDiff;

        if (yLevel >= 0 && yLevel < LEVEL_COUNT) {
          const intensity = Math.min(1, Math.log10(size + 1) / 5);
          rects.push({
            x,
            y: yLevel * LEVEL_HEIGHT,
            width: TICK_WIDTH,
            height: LEVEL_HEIGHT,
            fill: `rgba(255, 0, 0, ${intensity})`,
            key: `ask-${tIndex}-${price}`
          });
        }
      });
    });

    return rects;
  }, [history]);

  return (
    <div className="flex flex-col bg-[#0A0A0F] border border-gray-800 rounded-lg overflow-hidden">
      <div className="flex justify-between items-center px-4 py-2 bg-[#111] border-b border-gray-800">
        <span className="text-xs text-gray-400 font-mono">ORDERBOOK HEATMAP (±25 LEVELS)</span>
        <span className="text-[10px] text-gray-500 font-mono">X: TIME (60 TICKS) | Y: PRICE</span>
      </div>
      <div className="relative overflow-x-auto">
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto"
          preserveAspectRatio="none"
        >
          {heatmapData.map((rect) => (
            <rect
              key={rect.key}
              x={rect.x}
              y={rect.y}
              width={rect.width}
              height={rect.height}
              fill={rect.fill}
            />
          ))}
          {/* Mid-price line */}
          <line
            x1="0"
            y1={24.5 * LEVEL_HEIGHT}
            x2={width}
            y2={24.5 * LEVEL_HEIGHT}
            stroke="white"
            strokeDasharray="5,5"
            opacity="0.5"
          />
        </svg>
        {/* Y-Axis Labels */}
        <div className="absolute left-2 top-0 h-full flex flex-col justify-between py-2 pointer-events-none text-[8px] font-mono text-gray-500">
          <span>+25 LVL</span>
          <span>MID</span>
          <span>-25 LVL</span>
        </div>
      </div>
    </div>
  );
};

export default OrderbookHeatmap;
