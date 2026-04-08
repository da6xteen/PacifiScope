import React from 'react';
import Link from 'next/link';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white flex flex-col font-sans">
      <header className="border-b border-gray-800 bg-[#111] py-4 px-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[#1A73E8] rounded flex items-center justify-center font-bold">P</div>
          <h1 className="text-xl font-bold tracking-tight">PacifiScope</h1>
        </div>
        <nav className="flex items-center gap-4">
          <Link href="/" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Dashboard</Link>
          <Link href="/analysis" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Analysis</Link>
          <Link href="/about" className="text-sm font-bold text-[#1A73E8]">About</Link>
        </nav>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full p-8 space-y-12">
        <section className="space-y-4">
          <h2 className="text-3xl font-bold text-[#1A73E8]">About PacifiScope</h2>
          <p className="text-gray-300 leading-relaxed text-lg">
            PacifiScope is a real-time orderbook imbalance analytics engine designed specifically for the Pacifica ecosystem.
            By capturing high-frequency liquidity data and applying advanced metrics, we provide traders and researchers with
            unprecedented visibility into market dynamics and hidden whale activity.
          </p>
        </section>

        <section className="space-y-6">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-[#1A73E8] rounded-full"></span>
            System Architecture
          </h3>
          <div className="bg-[#111] p-8 border border-gray-800 rounded-xl overflow-hidden flex justify-center">
            {/* Raw SVG Architecture Diagram */}
            <svg width="600" height="350" viewBox="0 0 600 350" fill="none" xmlns="http://www.w3.org/2000/svg" className="max-w-full h-auto">
              {/* Nodes */}
              <rect x="20" y="140" width="120" height="60" rx="4" fill="#1A1A1F" stroke="#333" strokeWidth="2"/>
              <text x="80" y="175" fill="white" fontSize="12" textAnchor="middle" fontWeight="bold">Pacifica WS</text>

              <rect x="220" y="140" width="140" height="60" rx="4" fill="#1A73E8" fillOpacity="0.2" stroke="#1A73E8" strokeWidth="2"/>
              <text x="290" y="175" fill="white" fontSize="12" textAnchor="middle" fontWeight="bold">Collector Service</text>

              <rect x="440" y="60" width="120" height="60" rx="4" fill="#1A1A1F" stroke="#FF4500" strokeWidth="2"/>
              <text x="500" y="95" fill="white" fontSize="12" textAnchor="middle" fontWeight="bold">Redis (Pub/Sub)</text>

              <rect x="440" y="220" width="120" height="60" rx="4" fill="#1A1A1F" stroke="#00D1FF" strokeWidth="2"/>
              <text x="500" y="255" fill="white" fontSize="12" textAnchor="middle" fontWeight="bold">TimescaleDB</text>

              <circle cx="290" cy="30" r="25" fill="#111" stroke="#444" strokeWidth="2"/>
              <text x="290" y="35" fill="#666" fontSize="10" textAnchor="middle">Next.js</text>

              {/* Arrows */}
              <path d="M140 170 H220" stroke="#666" strokeWidth="2" markerEnd="url(#arrow)"/>
              <path d="M360 160 L440 100" stroke="#666" strokeWidth="2" markerEnd="url(#arrow)"/>
              <path d="M360 180 L440 240" stroke="#666" strokeWidth="2" markerEnd="url(#arrow)"/>
              <path d="M500 120 V220" stroke="#444" strokeWidth="1" strokeDasharray="4 4"/>

              <path d="M440 90 Q350 90 300 55" stroke="#1A73E8" strokeWidth="2" strokeDasharray="4 4" markerEnd="url(#arrow)"/>

              {/* Markers */}
              <defs>
                <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orientation="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L0,6 L9,3 z" fill="#666" />
                </marker>
              </defs>

              <text x="180" y="160" fill="#666" fontSize="9" textAnchor="middle">L2 Stream</text>
              <text x="400" y="120" fill="#666" fontSize="9" textAnchor="middle" transform="rotate(-30, 400, 120)">Real-time</text>
              <text x="400" y="220" fill="#666" fontSize="9" textAnchor="middle" transform="rotate(30, 400, 220)">Persistence</text>
            </svg>
          </div>
        </section>

        <section className="space-y-6">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-[#1A73E8] rounded-full"></span>
            Pacifica Integration
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             <div className="bg-[#111] border border-gray-800 rounded-lg overflow-hidden h-48 flex items-center justify-center text-gray-600 text-xs italic p-4 text-center">
                [Screenshot: Real-time orderbook stream from Pacifica WS]
             </div>
             <div className="bg-[#111] border border-gray-800 rounded-lg overflow-hidden h-48 flex items-center justify-center text-gray-600 text-xs italic p-4 text-center">
                [Screenshot: TimescaleDB hypertable ingestion metrics]
             </div>
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div className="space-y-4">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-[#1A73E8] rounded-full"></span>
              Core Features
            </h3>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li className="flex gap-2">
                <span className="text-[#1A73E8]">✓</span>
                <strong>Orderbook Heatmap:</strong> Visualizing liquidity depth across ±25 price levels.
              </li>
              <li className="flex gap-2">
                <span className="text-[#1A73E8]">✓</span>
                <strong>Weighted Imbalance:</strong> Advanced ratio using distance-to-mid weighting.
              </li>
              <li className="flex gap-2">
                <span className="text-[#1A73E8]">✓</span>
                <strong>Whale/Iceberg Detection:</strong> Tracking $50k+ orders and high-persistence liquidity.
              </li>
              <li className="flex gap-2">
                <span className="text-[#1A73E8]">✓</span>
                <strong>Predictive Alpha:</strong> Correlation engine between imbalance and price velocity.
              </li>
            </ul>
          </div>
          <div className="space-y-4">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-[#1A73E8] rounded-full"></span>
              Team Info
            </h3>
            <div className="p-4 bg-[#111] border border-gray-800 rounded-lg">
              <p className="text-gray-300 font-bold mb-1">Pacific Builders</p>
              <p className="text-gray-500 text-xs leading-relaxed">
                A group of decentralized finance enthusiasts and full-stack engineers dedicated to building robust infrastructure for the next generation of trading.
              </p>
            </div>
          </div>
        </section>

        <section className="pt-8 border-t border-gray-800 text-center">
          <p className="text-gray-500 text-xs uppercase tracking-widest mb-4">Built for the Pacifica Hackathon 2024</p>
          <div className="flex justify-center gap-4">
             <div className="w-10 h-10 bg-[#111] border border-gray-800 rounded flex items-center justify-center grayscale hover:grayscale-0 transition-all cursor-pointer">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.042-1.416-4.042-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
             </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-gray-800 bg-[#0A0A0F] py-6 text-center">
        <p className="text-[10px] text-gray-600 font-mono tracking-widest">PACIFISCOPE — OPEN SOURCE TRADING INTELLIGENCE</p>
      </footer>
    </div>
  );
}
