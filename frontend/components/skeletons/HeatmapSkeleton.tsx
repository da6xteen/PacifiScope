import React from 'react';

const HeatmapSkeleton = () => {
  return (
    <div className="flex flex-col bg-[#0A0A0F] border border-gray-800 rounded-lg overflow-hidden animate-pulse">
      <div className="flex justify-between items-center px-4 py-2 bg-[#111] border-b border-gray-800">
        <div className="h-3 w-48 bg-gray-800 rounded" />
        <div className="h-2 w-32 bg-gray-800 rounded" />
      </div>
      <div className="h-[500px] bg-[#0A0A0F] relative">
        <div className="absolute inset-0 flex flex-col justify-around py-10 px-4">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="h-[2px] w-full bg-gray-900/50" />
          ))}
        </div>
      </div>
    </div>
  );
};

export default HeatmapSkeleton;
