import React from 'react';

const ChartSkeleton = () => {
  return (
    <div className="bg-[#111] border border-gray-800 rounded-lg p-4 h-[300px] animate-pulse flex flex-col gap-4">
      <div className="flex justify-between">
        <div className="h-4 w-32 bg-gray-800 rounded" />
        <div className="h-4 w-24 bg-gray-800 rounded" />
      </div>
      <div className="flex-1 bg-gray-900/30 rounded" />
    </div>
  );
};

export default ChartSkeleton;
