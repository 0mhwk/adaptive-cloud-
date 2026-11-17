// frontend/src/components/layout/Layout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-black text-zinc-100 font-sans transition-colors">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-black">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 scrollbar-thin bg-black">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

