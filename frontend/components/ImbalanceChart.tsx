"use client";

import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useStore } from '../lib/store';

interface TooltipPayload {
  ts: number;
  imbalance: number;
  [key: string]: unknown;
}

interface TooltipProps {
  active?: boolean;
  payload?: { payload: TooltipPayload; value: number }[];
}

const CustomTooltip = ({ active, payload }: TooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1A1A1F] border border-gray-700 p-2 text-xs font-mono">
        <p className="text-gray-400">{new Date(payload[0].payload.ts).toLocaleTimeString()}</p>
        <p className={`${payload[0].value > 0 ? 'text-green-500' : 'text-red-500'}`}>
          Imbalance: {payload[0].value.toFixed(4)}
        </p>
      </div>
    );
  }
  return null;
};

const ImbalanceChart = () => {
  const history = useStore((state) => state.history);

  const data = useMemo(() => {
    return history.slice(-60).map(snapshot => {
      const bidVol = snapshot.bids.slice(0, 5).reduce((sum, level) => sum + level[1], 0);
      const askVol = snapshot.asks.slice(0, 5).reduce((sum, level) => sum + level[1], 0);
      const imbalance = bidVol + askVol === 0 ? 0 : (bidVol - askVol) / (bidVol + askVol);

      return {
        ts: snapshot.ts,
        imbalance
      };
    });
  }, [history]);

  return (
    <div className="h-48 w-full bg-[#0A0A0F] border border-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 font-mono mb-2 uppercase tracking-wider">Imbalance Ratio (Last 60 Ticks)</div>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorImbalance" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#1A73E8" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#1A73E8" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <XAxis
            dataKey="ts"
            hide
          />
          <YAxis
            domain={[-1, 1]}
            tick={{ fontSize: 10, fill: '#666' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="#333" />
          <Area
            type="monotone"
            dataKey="imbalance"
            stroke="#1A73E8"
            fillOpacity={1}
            fill="url(#colorImbalance)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ImbalanceChart;
