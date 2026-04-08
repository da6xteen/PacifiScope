"use client";

import React, { memo, useMemo } from 'react';
import { useStore } from '../lib/store';
import StatsBarSkeleton from './skeletons/StatsBarSkeleton';

const StatsBar = memo(() => {
  const lastSnapshot = useStore((state) => state.lastSnapshot);

  const stats = useMemo(() => {
    if (!lastSnapshot || !lastSnapshot.bids.length || !lastSnapshot.asks.length) {
      return { spreadBps: 0, midPrice: 0, imbalance: 0 };
    }

    const bestBid = lastSnapshot.bids[0][0];
    const bestAsk = lastSnapshot.asks[0][0];
    const midPrice = (bestBid + bestAsk) / 2;
    const spreadBps = ((bestAsk - bestBid) / midPrice) * 10000;

    const bidVol = lastSnapshot.bids.slice(0, 5).reduce((sum, level) => sum + level[1], 0);
    const askVol = lastSnapshot.asks.slice(0, 5).reduce((sum, level) => sum + level[1], 0);
    const imbalance = (bidVol - askVol) / (bidVol + askVol);

    return { spreadBps, midPrice, imbalance };
  }, [lastSnapshot]);

  if (!lastSnapshot) {
    return <StatsBarSkeleton />;
  }

  return (
    <div className="flex flex-wrap gap-4 p-4 bg-[#111] border-b border-gray-800 text-sm font-mono h-[81px]">
      <div className="flex flex-col">
        <span className="text-gray-400">MID PRICE</span>
        <span className="text-white text-lg">{stats.midPrice.toFixed(2)}</span>
      </div>
      <div className="flex flex-col">
        <span className="text-gray-400">SPREAD (BPS)</span>
        <span className={`text-lg ${stats.spreadBps < 10 ? 'text-green-500' : 'text-yellow-500'}`}>
          {stats.spreadBps.toFixed(2)}
        </span>
      </div>
      <div className="flex flex-col">
        <span className="text-gray-400">IMBALANCE</span>
        <div className="flex items-center gap-2">
          <span className={`text-lg ${stats.imbalance > 0 ? 'text-green-500' : 'text-red-500'}`}>
            {stats.imbalance.toFixed(3)}
          </span>
          <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full ${stats.imbalance > 0 ? 'bg-green-500' : 'bg-red-500'}`}
              style={{
                width: `${Math.abs(stats.imbalance) * 100}%`,
                marginLeft: stats.imbalance > 0 ? '50%' : `${50 - Math.abs(stats.imbalance) * 50}%`
              }}
            />
          </div>
        </div>
      </div>
      <div className="flex flex-col ml-auto text-right">
        <span className="text-gray-400">LAST UPDATE</span>
        <span className="text-gray-500">{new Date(lastSnapshot.ts).toLocaleTimeString()}</span>
      </div>
    </div>
  );
});

StatsBar.displayName = 'StatsBar';

export default StatsBar;
