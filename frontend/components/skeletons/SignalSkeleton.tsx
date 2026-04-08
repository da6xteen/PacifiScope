import React from 'react';

const SignalSkeleton = () => {
  return (
    <div className="bg-[#111] border border-gray-800 rounded-lg overflow-hidden animate-pulse">
      <div className="px-4 py-2 border-b border-gray-800 flex justify-between items-center">
        <div className="h-3 w-24 bg-gray-800 rounded" />
        <div className="h-3 w-16 bg-gray-800 rounded" />
      </div>
      <div className="p-3 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-2">
            <div className="flex justify-between">
              <div className="h-4 w-12 bg-gray-700 rounded" />
              <div className="h-4 w-16 bg-gray-700 rounded" />
            </div>
            <div className="h-2 w-full bg-gray-800 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
};

export default SignalSkeleton;
