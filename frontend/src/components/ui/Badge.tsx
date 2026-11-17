// frontend/src/components/ui/Badge.tsx
import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export type BadgeVariant =
  | 'neutral'
  | 'indigo'
  | 'white'
  | 'emerald'
  | 'amber'
  | 'rose'
  | 'outline'
  | 'success'
  | 'warning'
  | 'danger';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export function Badge({ children, variant = 'neutral', className, ...props }: BadgeProps) {
  const variantStyles: Record<BadgeVariant, string> = {
    neutral: 'bg-zinc-900 text-zinc-300 border border-zinc-800',
    indigo: 'bg-white text-black font-semibold border border-white',
    white: 'bg-white text-black font-semibold border border-white',
    emerald: 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/60',
    amber: 'bg-amber-950/60 text-amber-300 border border-amber-800/60',
    rose: 'bg-rose-950/60 text-rose-300 border border-rose-800/60',
    outline: 'border border-zinc-700 text-zinc-200 bg-transparent',
    success: 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/60',
    warning: 'bg-amber-950/60 text-amber-300 border border-amber-800/60',
    danger: 'bg-rose-950/60 text-rose-300 border border-rose-800/60',
  };

  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide',
          variantStyles[variant],
          className
        )
      )}
      {...props}
    >
      {children}
    </span>
  );
}
