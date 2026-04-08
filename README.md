# 🌊 PacifiScope

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Next.js Version](https://img.shields.io/badge/next.js-14.2.35-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Hackathon Track](https://img.shields.io/badge/Hackathon-Track%202-orange.svg)](https://pacifica.fi)

**PacifiScope** is a high-performance, real-time orderbook imbalance analytics dashboard built specifically for the Pacifica ecosystem. It provides traders with deep visibility into market microstructures, liquidity concentrations, and whale behavior through a sophisticated data pipeline and intuitive visualizations.

## 🚀 Key Features

- **Real-Time Heatmap (±25 Levels):** Visualizes orderbook depth and liquidity concentration updates every 500ms.
- **Weighted Imbalance Ratio:** Calculates a proximity-weighted ratio using a custom distance-to-mid formula.
- **Whale & Iceberg Detection:** Automated alerts for orders exceeding $50k USD and high-persistence "iceberg" patterns.
- **Alpha Correlation Engine:** Historical analysis of the relationship between imbalance and future price movement.
- **Multi-Market Comparison:** Side-by-side view of multiple symbols with synchronized charting.
- **Demo Mode:** Full system replay functionality using historical data for offline demos.

## 🏗️ Architecture

PacifiScope is built as a robust microservices architecture:

- **Collector (Python):** High-frequency WebSocket ingestion from Pacifica, metric computation, and TimescaleDB persistence.
- **API (FastAPI):** Asynchronous backend handling REST queries and WebSocket relay for real-time frontend updates.
- **Frontend (Next.js 14):** Modern React dashboard with Server Components, SWR for data fetching, and Recharts for visualization.
- **TimescaleDB:** Time-series optimized PostgreSQL extension for high-performance market data analytics.
- **Redis:** Low-latency Pub/Sub for sub-100ms real-time data propagation.

## 📸 Screenshots

| Dashboard Overview | Historical Analysis |
|:---:|:---:|
| ![Dashboard Placeholder](https://via.placeholder.com/400x250?text=Dashboard+Screenshot) | ![Analysis Placeholder](https://via.placeholder.com/400x250?text=Analysis+Screenshot) |

## 🎥 Demo Video

[Watch the Demo on Loom](https://www.loom.com/share/placeholder)

## 🛠️ Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd pacifiscope
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

3. **Start the services with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Access the dashboard**
   Open your browser at `http://localhost:3000`.

*To run in Demo Mode, set `DEMO_MODE=true` in your `.env` file.*

## 📈 Service Ports

| Service       | Port | Description |
|---------------|------|-------------|
| Frontend      | 3000 | Next.js Dashboard |
| API           | 8000 | FastAPI REST/WS |
| TimescaleDB   | 5432 | Persistence Layer |
| Redis         | 6379 | Real-time Bus |
| Prometheus    | 8001 | Collector Metrics |

---
Built with ❤️ by the Pacific Builders Team for the Pacifica Hackathon 2024.
