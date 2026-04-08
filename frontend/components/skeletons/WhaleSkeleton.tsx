import React from 'react';

const WhaleSkeleton = () => {
  return (
    <div className="bg-[#111] border border-gray-800 rounded-lg flex flex-col h-[400px] animate-pulse">
      <div className="p-3 border-b border-gray-800 flex justify-between items-center bg-[#151515]">
        <div className="h-3 w-32 bg-gray-800 rounded" />
        <div className="h-2 w-16 bg-gray-800 rounded" />
      </div>
      <div className="flex-1 p-4 space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex gap-3">
            <div className="h-8 w-8 bg-gray-800 rounded-full" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-1/2 bg-gray-700 rounded" />
              <div className="h-2 w-1/4 bg-gray-800 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WhaleSkeleton;
