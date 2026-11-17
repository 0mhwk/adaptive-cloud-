// frontend/src/components/layout/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  Search,
  Zap,
  Activity,
  Cloud,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Attack Detection', path: '/', icon: ShieldAlert, desc: 'Threat classification & live alerts' },
  { name: 'Root Cause Analysis', path: '/rca', icon: Search, desc: 'Evidence-based forensic RCA' },
  { name: 'Self-Healing', path: '/healing', icon: Zap, desc: 'Autonomous playbooks & approval gate' },
  { name: 'Predictive Maintenance', path: '/maintenance', icon: Activity, desc: 'Failure probability & system health' },
];

export function Sidebar() {
  return (
    <aside className="w-60 flex-shrink-0 border-r border-zinc-900 bg-black flex flex-col h-screen select-none">
      {/* Brand */}
      <div className="h-16 flex items-center px-5 border-b border-zinc-900 space-x-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-black shadow">
          <Cloud className="h-4 w-4 stroke-[2.5]" />
        </div>
        <div>
          <span className="text-sm font-bold tracking-tight text-white">AdaptiveCloud</span>
          <span className="block text-[10px] text-zinc-500 font-mono tracking-widest uppercase">Security · AI</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-5 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `group flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-white text-black font-bold shadow'
                    : 'text-zinc-400 hover:bg-zinc-900 hover:text-white'
                }`
              }
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span className="truncate">{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-zinc-900 space-y-1.5">
        <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500">
          <span>AWS Region</span>
          <span className="text-green-400 font-semibold">ap-south-1 ✓</span>
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500">
          <span>UNSW-NB15 Dataset</span>
          <span className="text-blue-400 font-semibold">257,673 flows</span>
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500">
          <span>Approval Gate</span>
          <span className="text-white font-semibold">ACTIVE</span>
        </div>
      </div>
    </aside>
  );
}
