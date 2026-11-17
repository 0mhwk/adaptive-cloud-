// frontend/src/components/ui/Card.tsx
import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

export function Card({ children, className, header, footer, ...props }: CardProps) {
  return (
    <div
      className={twMerge(
        clsx(
          'rounded-2xl border border-zinc-800 bg-[#09090b] text-white overflow-hidden transition-colors',
          className
        )
      )}
      {...props}
    >
      {header && <div className="px-6 py-4 border-b border-zinc-800 font-medium text-white">{header}</div>}
      <div className="p-6">{children}</div>
      {footer && <div className="px-6 py-3 border-t border-zinc-800 bg-black text-xs text-zinc-400">{footer}</div>}
    </div>
  );
}
