import { create } from 'zustand';

interface OrderbookSnapshot {
  symbol: string;
  bids: [number, number][];
  asks: [number, number][];
  ts: number;
}

interface AppState {
  currentSymbol: string;
  setSymbol: (symbol: string) => void;
  lastSnapshot: OrderbookSnapshot | null;
  setSnapshot: (snapshot: OrderbookSnapshot) => void;
  history: OrderbookSnapshot[];
  maxHistory: number;
}

export const useStore = create<AppState>((set) => ({
  currentSymbol: '',
  setSymbol: (symbol) => set({
    currentSymbol: symbol,
    lastSnapshot: null,
    history: []
  }),
  lastSnapshot: null,
  setSnapshot: (snapshot) => set((state) => {
    const newHistory = [...state.history, snapshot].slice(-state.maxHistory);
    return {
      lastSnapshot: snapshot,
      history: newHistory
    };
  }),
  history: [],
  maxHistory: 100, // Sufficient for 60 ticks heatmap
}));
