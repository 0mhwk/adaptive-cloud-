// frontend/src/components/ui/StatTile.tsx
import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface StatTileProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  className?: string;
}

export function StatTile({ label, value, subtext, icon, trend, className }: StatTileProps) {
  return (
    <div
      className={twMerge(
        clsx(
          'p-5 rounded-2xl border border-zinc-800 bg-[#09090b] flex flex-col justify-between transition-colors',
          className
        )
      )}
    >
      <div className="flex items-center justify-between text-zinc-400">
        <span className="text-[11px] font-mono uppercase tracking-wider">{label}</span>
        {icon && <span className="text-zinc-400">{icon}</span>}
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <div className="text-2xl font-bold tracking-tight text-white">{value}</div>
        {trend && (
          <span
            className={clsx(
              'text-xs font-medium',
              trend.isPositive ? 'text-emerald-400' : 'text-zinc-400'
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtext && <div className="mt-1 text-xs text-zinc-400">{subtext}</div>}
    </div>
  );
}
