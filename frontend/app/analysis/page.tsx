"use client";

import React, { useMemo } from 'react';
import Link from 'next/link';
import useSWR from 'swr';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import MarketSelector from '../../components/MarketSelector';
import { useStore } from '../../lib/store';

const fetcher = (url: string) => fetch(url).then(res => res.json());

const AnalysisPage = () => {
  const currentSymbol = useStore((state) => state.currentSymbol);

  const { data: correlationData, isLoading: corrLoading } = useSWR(
    currentSymbol ? `/api/analysis/correlation/${currentSymbol}?days=7` : null,
    fetcher
  );

  const { data: heatmapData, isLoading: heatmapLoading } = useSWR(
    currentSymbol ? `/api/analysis/heatmap/${currentSymbol}` : null,
    fetcher
  );

  const scatterPoints = useMemo(() => {
    if (!correlationData?.data) return [];
    return correlationData.data.map((d: {x: number, y: number}) => ({
      ...d,
      color: (d.x > 0 && d.y > 0) || (d.x < 0 && d.y < 0) ? '#10b981' : '#ef4444'
    }));
  }, [correlationData]);

  const renderHeatmap = () => {
    if (!heatmapData?.grid) return null;

    const days = Array.from(new Set(heatmapData.grid.map((d: {date: string}) => d.date))).sort().reverse();
    const hours = Array.from({ length: 24 }, (_, i) => i);

    const rowHeight = 24; // px

    return (
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 800 ${days.length * rowHeight + 40}`} className="w-full min-w-[600px]">
          {/* X Axis (Hours) */}
          {hours.map(h => (
            <text key={h} x={40 + h * 30 + 15} y={20} fill="#666" fontSize="10" textAnchor="middle">
              {h}h
            </text>
          ))}

          {/* Grid Rows */}
          {days.map((date, i) => (
            <g key={date} transform={`translate(0, ${40 + i * rowHeight})`}>
              <text x={0} y={15} fill="#666" fontSize="10">{date.slice(5)}</text>
              {hours.map(h => {
                const cell = heatmapData.grid.find((d: {date: string, hour: number, value: number}) => d.date === date && d.hour === h);
                const val = cell?.value || 0;
                // Color scale: Blue (-1) to Red (1)
                let color = "#1A1A1F";
                if (val > 0) {
                  const opacity = Math.min(1, val * 2);
                  color = `rgba(239, 68, 68, ${opacity})`;
                } else if (val < 0) {
                  const opacity = Math.min(1, Math.abs(val) * 2);
                  color = `rgba(59, 130, 246, ${opacity})`;
                }

                return (
                  <rect
                    key={h}
                    x={40 + h * 30}
                    y={0}
                    width={28}
                    height={rowHeight - 4}
                    fill={color}
                    rx={2}
                  >
                    <title>{date} {h}:00 - Imbalance: {val.toFixed(4)}</title>
                  </rect>
                );
              })}
            </g>
          ))}
        </svg>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white flex flex-col">
      <header className="border-b border-gray-800 bg-[#111] py-4 px-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[#1A73E8] rounded flex items-center justify-center font-bold">P</div>
          <h1 className="text-xl font-bold tracking-tight">PacifiScope</h1>
        </div>
        <div className="flex items-center gap-6">
          <nav className="flex items-center gap-4 mr-2">
            <Link href="/" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Dashboard</Link>
            <Link href="/analysis" className="text-sm font-bold text-[#1A73E8]">Analysis</Link>
          </nav>
        </div>
      </header>

      <main className="flex-1 flex flex-col max-w-[1400px] mx-auto w-full p-4 gap-6">
        <div className="w-full md:w-64">
          <MarketSelector />
        </div>

        {/* Predictive Score Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#111] border border-gray-800 rounded-lg p-6">
            <h3 className="text-xs text-gray-500 font-mono uppercase mb-2">Correlation Coefficient</h3>
            {corrLoading ? (
              <div className="h-10 w-24 bg-gray-800 animate-pulse rounded" />
            ) : (
              <div className="text-3xl font-bold text-[#1A73E8]">
                {correlationData?.correlation?.toFixed(4) || '0.0000'}
              </div>
            )}
            <p className="text-[10px] text-gray-600 mt-2">Pearson&apos;s r (Imbalance vs 5m Price Change)</p>
          </div>
          <div className="bg-[#111] border border-gray-800 rounded-lg p-6">
            <h3 className="text-xs text-gray-500 font-mono uppercase mb-2">Predictive Power (R²)</h3>
            {corrLoading ? (
              <div className="h-10 w-24 bg-gray-800 animate-pulse rounded" />
            ) : (
              <div className="text-3xl font-bold text-white">
                {((correlationData?.r_squared || 0) * 100).toFixed(2)}%
              </div>
            )}
            <p className="text-[10px] text-gray-600 mt-2">Variance in price explained by imbalance</p>
          </div>
          <div className="bg-[#111] border border-gray-800 rounded-lg p-6">
            <h3 className="text-xs text-gray-500 font-mono uppercase mb-2">Sample Size</h3>
            {corrLoading ? (
              <div className="h-10 w-24 bg-gray-800 animate-pulse rounded" />
            ) : (
              <div className="text-3xl font-bold text-gray-400">
                {correlationData?.sample_size?.toLocaleString() || '0'}
              </div>
            )}
            <p className="text-[10px] text-gray-600 mt-2">1-minute data points over last 7 days</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Correlation Chart */}
          <div className="bg-[#111] border border-gray-800 rounded-lg p-6 flex flex-col h-[500px]">
            <h3 className="text-sm font-bold mb-6 flex items-center justify-between">
              Imbalance/Price Correlation
              <span className="text-[10px] font-mono text-gray-500 uppercase">Last 7 Days (sampled)</span>
            </h3>
            <div className="flex-1 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                  <XAxis
                    type="number"
                    dataKey="x"
                    name="Imbalance"
                    unit=""
                    stroke="#666"
                    fontSize={10}
                    label={{ value: 'Imbalance Ratio', position: 'insideBottom', offset: -10, fill: '#666', fontSize: 10 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="y"
                    name="Price Change"
                    unit="bps"
                    stroke="#666"
                    fontSize={10}
                    label={{ value: 'Next 5m Price Change (bps)', angle: -90, position: 'insideLeft', fill: '#666', fontSize: 10 }}
                  />
                  <ZAxis type="number" range={[20, 20]} />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ backgroundColor: '#111', border: '1px solid #333', fontSize: '10px' }}
                  />
                  <Scatter name="Data Points" data={scatterPoints}>
                    {scatterPoints.map((entry: {color: string}, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.6} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Heatmap */}
          <div className="bg-[#111] border border-gray-800 rounded-lg p-6 flex flex-col">
            <h3 className="text-sm font-bold mb-6 flex items-center justify-between">
              Imbalance Seasonality
              <span className="text-[10px] font-mono text-gray-500 uppercase">Avg Imbalance by Hour (14d)</span>
            </h3>
            <div className="flex-1">
              {heatmapLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 14 }).map((_, i) => (
                    <div key={i} className="h-4 w-full bg-gray-800 animate-pulse rounded" />
                  ))}
                </div>
              ) : (
                renderHeatmap()
              )}
            </div>
            <div className="mt-6 flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500" />
                <span className="text-[10px] text-gray-500">Sell Pressure</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500" />
                <span className="text-[10px] text-gray-500">Buy Pressure</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-800 bg-[#0A0A0F] py-3 px-6 text-center">
        <p className="text-[10px] text-gray-600 font-mono">PACIFISCOPE — HISTORICAL ANALYTICS ENGINE</p>
      </footer>
    </div>
  );
};

export default AnalysisPage;
