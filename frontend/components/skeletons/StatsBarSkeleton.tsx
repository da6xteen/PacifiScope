import React from 'react';

const StatsBarSkeleton = () => {
  return (
    <div className="flex flex-wrap gap-4 p-4 bg-[#111] border-b border-gray-800 text-sm font-mono animate-pulse h-[81px]">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex flex-col gap-2">
          <div className="h-3 w-16 bg-gray-800 rounded" />
          <div className="h-6 w-24 bg-gray-700 rounded" />
        </div>
      ))}
      <div className="flex flex-col ml-auto text-right gap-2">
        <div className="h-3 w-20 bg-gray-800 rounded" />
        <div className="h-4 w-16 bg-gray-700 rounded" />
      </div>
    </div>
  );
};

export default StatsBarSkeleton;
