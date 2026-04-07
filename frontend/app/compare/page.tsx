"use client";

import React, { useState, useMemo, createContext, useContext, useCallback } from 'react';
import Link from 'next/link';
import useSWR from 'swr';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import Papa from 'papaparse';
import { Download } from 'lucide-react';

const fetcher = (url: string) => fetch(url).then(res => res.json());

// --- Types ---
interface MetricPoint {
  time: string;
  imbalance_ratio: number | null;
  spread_bps: number | null;
}

interface ComparisonData {
  [symbol: string]: MetricPoint[];
}

// --- Sync Context ---
interface ChartSyncContextType {
  syncId: string;
  xDomain: [number | string, number | string] | null;
  setXDomain: (domain: [number | string, number | string] | null) => void;
}

const ChartSyncContext = createContext<ChartSyncContextType>({
  syncId: 'compare-sync',
  xDomain: null,
  setXDomain: () => {},
});

// --- Components ---

interface TooltipProps {
  active?: boolean;
  payload?: { value: number | null; payload: MetricPoint }[];
}

const CustomTooltip = ({ active, payload }: TooltipProps) => {
  if (active && payload && payload.length) {
    const val = payload[0].value;
    return (
      <div className="bg-[#1A1A1F] border border-gray-700 p-2 text-[10px] font-mono">
        <p className="text-gray-400">{new Date(payload[0].payload.time).toLocaleTimeString()}</p>
        <p className={`${val !== null && val > 0 ? 'text-green-500' : val !== null && val < 0 ? 'text-red-500' : 'text-gray-400'}`}>
          Imbalance: {val !== null ? val.toFixed(4) : 'N/A'}
        </p>
      </div>
    );
  }
  return null;
};

const ComparisonChart = ({ symbol, data, yDomain }: { symbol: string; data: MetricPoint[]; yDomain: [number, number] }) => {
  const { syncId, xDomain, setXDomain } = useContext(ChartSyncContext);
  const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
  const [refAreaRight, setRefAreaRight] = useState<string | null>(null);

  const zoom = () => {
    if (refAreaLeft === refAreaRight || refAreaRight === null) {
      setRefAreaLeft(null);
      setRefAreaRight(null);
      return;
    }

    let [left, right] = [refAreaLeft!, refAreaRight!];
    if (new Date(left).getTime() > new Date(right).getTime()) [left, right] = [right, left];

    setXDomain([left, right]);
    setRefAreaLeft(null);
    setRefAreaRight(null);
  };

  const zoomOut = () => {
    setXDomain(null);
  };

  return (
    <div className="bg-[#111] border border-gray-800 rounded-lg p-3 flex flex-col h-48">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">{symbol}</span>
        {xDomain && (
          <button onClick={zoomOut} className="text-[8px] text-[#1A73E8] hover:underline font-mono">RESET ZOOM</button>
        )}
      </div>
      <div className="flex-1 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 5, right: 5, left: -25, bottom: 0 }}
            syncId={syncId}
            onMouseDown={(e) => e && setRefAreaLeft(e.activeLabel as string)}
            onMouseMove={(e) => e && refAreaLeft && setRefAreaRight(e.activeLabel as string)}
            onMouseUp={zoom}
          >
            <defs>
              <linearGradient id={`color-${symbol}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1A73E8" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#1A73E8" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              hide
              domain={xDomain || ['auto', 'auto']}
              type="category"
              allowDataOverflow
            />
            <YAxis
              domain={yDomain}
              tick={{ fontSize: 9, fill: '#444' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} isAnimationActive={false} />
            <ReferenceLine y={0} stroke="#222" />
            <Area
              type="monotone"
              dataKey="imbalance_ratio"
              stroke="#1A73E8"
              fillOpacity={1}
              fill={`url(#color-${symbol})`}
              isAnimationActive={false}
              connectNulls
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const CorrelationHeatmap = ({ symbols, data }: { symbols: string[]; data: ComparisonData }) => {
  const matrix = useMemo(() => {
    const size = symbols.length;
    const m = Array(size).fill(0).map(() => Array(size).fill(0));

    for (let i = 0; i < size; i++) {
      for (let j = 0; j < size; j++) {
        if (i === j) {
          m[i][j] = 1;
          continue;
        }

        const s1 = symbols[i];
        const s2 = symbols[j];
        const d1 = data[s1].map(p => p.imbalance_ratio);
        const d2 = data[s2].map(p => p.imbalance_ratio);

        // Filter out nulls and ensure alignment
        const pairs: [number, number][] = [];
        for (let k = 0; k < d1.length; k++) {
          if (d1[k] !== null && d2[k] !== null) {
            pairs.push([d1[k]!, d2[k]!]);
          }
        }

        if (pairs.length < 2) {
          m[i][j] = 0;
          continue;
        }

        const x = pairs.map(p => p[0]);
        const y = pairs.map(p => p[1]);
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((a, b, idx) => a + b * y[idx], 0);
        const sumX2 = x.reduce((a, b) => a + b * b, 0);
        const sumY2 = y.reduce((a, b) => a + b * b, 0);

        const numerator = n * sumXY - sumX * sumY;
        const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

        m[i][j] = denominator === 0 ? 0 : numerator / denominator;
      }
    }
    return m;
  }, [symbols, data]);

  return (
    <div className="bg-[#111] border border-gray-800 rounded-lg p-6">
      <h3 className="text-xs font-bold text-gray-500 uppercase mb-6">Cross-Symbol Correlation Matrix</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-[10px] border-collapse">
          <thead>
            <tr>
              <th className="p-2"></th>
              {symbols.map(s => (
                <th key={s} className="p-2 text-gray-400 font-mono rotate-45 h-16 align-bottom">{s}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {symbols.map((s1, i) => (
              <tr key={s1}>
                <td className="p-2 text-gray-400 font-mono border-r border-gray-800">{s1}</td>
                {symbols.map((s2, j) => {
                  const val = matrix[i][j];
                  // Blue (-1) to Red (+1)
                  let bg = 'transparent';
                  if (val > 0) bg = `rgba(239, 68, 68, ${val})`;
                  else if (val < 0) bg = `rgba(59, 130, 246, ${Math.abs(val)})`;

                  return (
                    <td
                      key={s2}
                      className="p-2 text-center border border-gray-800/50"
                      style={{ backgroundColor: bg }}
                    >
                      {val.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Page ---

export default function ComparePage() {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [xDomain, setXDomain] = useState<[number | string, number | string] | null>(null);

  const { data: allMarkets } = useSWR('/api/markets', fetcher);

  const symbolsQuery = selectedSymbols.join(',');
  const { data: compareData } = useSWR<ComparisonData>(
    selectedSymbols.length > 0 ? `/api/compare?symbols=${symbolsQuery}&limit=100` : null,
    fetcher
  );

  const handleToggleSymbol = (symbol: string) => {
    if (selectedSymbols.includes(symbol)) {
      setSelectedSymbols(prev => prev.filter(s => s !== symbol));
    } else if (selectedSymbols.length < 6) {
      setSelectedSymbols(prev => [...prev, symbol]);
    }
  };

  const handleExportCSV = useCallback(() => {
    if (!compareData || selectedSymbols.length === 0) return;

    // We can use the first symbol's data length as they are aligned
    const firstSymbol = selectedSymbols[0];
    const dataPoints = compareData[firstSymbol];

    const exportData = dataPoints.map((_: MetricPoint, idx: number) => {
      const row: Record<string, string | number | null> = { time: dataPoints[idx].time };
      selectedSymbols.forEach(symbol => {
        row[`${symbol}_imbalance`] = compareData[symbol][idx].imbalance_ratio;
        row[`${symbol}_spread`] = compareData[symbol][idx].spread_bps;
      });
      return row;
    });

    const csv = Papa.unparse(exportData);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `pacifiscope_compare_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [compareData, selectedSymbols]);

  return (
    <ChartSyncContext.Provider value={{ syncId: 'compare-sync', xDomain, setXDomain }}>
      <div className="min-h-screen bg-[#0A0A0F] text-white flex flex-col">
        <header className="border-b border-gray-800 bg-[#111] py-4 px-6 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#1A73E8] rounded flex items-center justify-center font-bold">P</div>
            <h1 className="text-xl font-bold tracking-tight">PacifiScope</h1>
          </div>
          <div className="flex items-center gap-6">
            <nav className="flex items-center gap-4 mr-2">
              <Link href="/" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Dashboard</Link>
              <Link href="/analysis" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Analysis</Link>
              <Link href="/compare" className="text-sm font-bold text-[#1A73E8]">Compare</Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 p-6 max-w-[1600px] mx-auto w-full space-y-6">
          {/* Controls */}
          <div className="flex flex-wrap items-center justify-between gap-4 bg-[#111] border border-gray-800 p-4 rounded-lg">
            <div className="flex flex-col gap-2">
              <span className="text-xs text-gray-500 font-mono uppercase">Select Symbols (Max 6)</span>
              <div className="flex flex-wrap gap-2">
                {allMarkets?.map((symbol: string) => (
                  <button
                    key={symbol}
                    onClick={() => handleToggleSymbol(symbol)}
                    className={`px-3 py-1 text-xs rounded transition-colors border ${
                      selectedSymbols.includes(symbol)
                        ? 'bg-[#1A73E8] border-[#1A73E8] text-white'
                        : 'bg-[#1A1A1F] border-gray-700 text-gray-400 hover:border-gray-500'
                    }`}
                  >
                    {symbol}
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={handleExportCSV}
              disabled={!compareData}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-xs font-bold transition-colors"
            >
              <Download size={14} />
              EXPORT CSV
            </button>
          </div>

          {/* Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {selectedSymbols.length === 0 ? (
              <div className="col-span-full h-64 flex items-center justify-center border-2 border-dashed border-gray-800 rounded-lg text-gray-600">
                Select symbols above to start comparison
              </div>
            ) : (
              selectedSymbols.map(symbol => (
                <ComparisonChart
                  key={symbol}
                  symbol={symbol}
                  data={compareData?.[symbol] || []}
                  yDomain={[-1, 1]}
                />
              ))
            )}
          </div>

          {/* Correlation Matrix */}
          {selectedSymbols.length > 1 && compareData && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <CorrelationHeatmap symbols={selectedSymbols} data={compareData} />
              <div className="bg-[#111] border border-gray-800 rounded-lg p-6">
                <h3 className="text-xs font-bold text-gray-500 uppercase mb-4">Comparison Insights</h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Traders can identify lead-lag relationships by observing synchronized imbalance shifts.
                  High positive correlation suggests these markets move in tandem under similar buy/sell pressure.
                  Strong divergence may indicate relative value opportunities or impending volatility.
                </p>
                <div className="mt-6 flex gap-4">
                   <div className="flex flex-col">
                      <span className="text-[10px] text-gray-500 uppercase mb-1">Time Scale</span>
                      <span className="text-xs font-bold">1m Interval</span>
                   </div>
                   <div className="flex flex-col">
                      <span className="text-[10px] text-gray-500 uppercase mb-1">Data Window</span>
                      <span className="text-xs font-bold">100 Samples</span>
                   </div>
                </div>
              </div>
            </div>
          )}
        </main>

        <footer className="border-t border-gray-800 bg-[#0A0A0F] py-3 px-6 text-center">
          <p className="text-[10px] text-gray-600 font-mono uppercase">PACIFISCOPE — MULTI-SYMBOL COMPARISON ENGINE</p>
        </footer>
      </div>
    </ChartSyncContext.Provider>
  );
}
