"use client";

import React, { useEffect } from 'react';
import useSWR from 'swr';
import { useStore } from '../lib/store';

const fetcher = (url: string) => fetch(url).then(res => res.json());

const MarketSelector = () => {
  const currentSymbol = useStore((state) => state.currentSymbol);
  const setSymbol = useStore((state) => state.setSymbol);

  const { data: markets, error } = useSWR('/api/markets', fetcher);

  useEffect(() => {
    if (markets && markets.length > 0 && !currentSymbol) {
      setSymbol(markets[0]);
    }
  }, [markets, currentSymbol, setSymbol]);

  if (error) return <div className="p-4 text-red-500">Error loading markets</div>;
  if (!markets) return <div className="p-4 text-gray-500">Loading markets...</div>;

  return (
    <div className="flex items-center gap-4 p-4 bg-[#111] border-b border-gray-800">
      <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Market</span>
      <select
        value={currentSymbol}
        onChange={(e) => setSymbol(e.target.value)}
        className="bg-[#1A1A1F] text-white border border-gray-700 rounded px-3 py-1 outline-none focus:border-[#1A73E8]"
      >
        {markets.map((symbol: string) => (
          <option key={symbol} value={symbol}>
            {symbol}
          </option>
        ))}
      </select>
    </div>
  );
};

export default MarketSelector;
