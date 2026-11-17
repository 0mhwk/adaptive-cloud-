// frontend/src/pages/AttackDetectionPage.tsx
// Page 1: Attack Detection & Classification
// Shows live incidents from UNSW-NB15 dataset + AWS + local hosts
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/api/client';
import { ShieldAlert, Wifi, Server, Laptop, AlertTriangle, CheckCircle2, Clock, RefreshCw, Cloud } from 'lucide-react';

// ── Types ─────────────────────────────────────────────────────────────────────
interface LiveIncident {
  incident_id: string;
  timestamp: string;
  source: string;
  host_id: string;
  tier1_family: string;
  tier1_confidence: number;
  tier2_technique: string | null;
  tier2_confidence: number | null;
  status: string;
  features: Record<string, any>;
  rca?: { summary?: string };
}

interface LiveHost {
  id: string;
  display_label: string;
  ip_address: string;
  status: string;
  cpu: number;
  mem: number;
  is_cloud?: boolean;
  is_physical?: boolean;
  os_version?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const FAMILY_LABEL: Record<string, string> = {
  ddos: 'DDoS Flood',
  dos: 'DoS Attack',
  brute_force: 'Brute Force',
  port_scan: 'Port Scan',
  port_scan_recon: 'Reconnaissance',
  web_attack: 'Web Exploit',
  cryptomining: 'Crypto Mining',
  botnet: 'Botnet / C2',
  infiltration: 'Shellcode / RCE',
  exploit_other: 'Exploit',
  cloud_iam: 'IAM Abuse',
  cloud_storage: 'Data Exfil',
  privilege_escalation: 'Priv Escalation',
  benign: 'Normal',
};

const FAMILY_COLOR: Record<string, string> = {
  ddos: 'bg-red-500/15 text-red-400 border border-red-500/30',
  dos: 'bg-red-500/15 text-red-400 border border-red-500/30',
  brute_force: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
  port_scan: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  port_scan_recon: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  web_attack: 'bg-purple-500/15 text-purple-400 border border-purple-500/30',
  cryptomining: 'bg-pink-500/15 text-pink-400 border border-pink-500/30',
  botnet: 'bg-rose-500/15 text-rose-400 border border-rose-500/30',
  infiltration: 'bg-red-600/15 text-red-300 border border-red-600/30',
  exploit_other: 'bg-orange-600/15 text-orange-300 border border-orange-600/30',
  cloud_iam: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  privilege_escalation: 'bg-red-500/15 text-red-400 border border-red-500/30',
  benign: 'bg-green-500/15 text-green-400 border border-green-500/30',
};

function FamilyBadge({ family }: { family: string }) {
  const cls = FAMILY_COLOR[family] ?? 'bg-zinc-700/40 text-zinc-400 border border-zinc-700';
  const label = FAMILY_LABEL[family] ?? family.replace(/_/g, ' ');
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold font-mono uppercase ${cls}`}>
      {label}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    awaiting_approval: 'bg-amber-500/20 text-amber-400',
    ready_for_review: 'bg-blue-500/20 text-blue-400',
    approved: 'bg-green-500/20 text-green-400',
    rejected: 'bg-zinc-700 text-zinc-400',
    recorded: 'bg-zinc-700 text-zinc-400',
    executed: 'bg-green-600/20 text-green-300',
    healed: 'bg-emerald-500/20 text-emerald-400',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize ${map[status] ?? 'bg-zinc-700 text-zinc-400'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

function ConfBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 90 ? 'bg-red-500' : pct >= 75 ? 'bg-orange-400' : 'bg-yellow-400';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 rounded-full bg-zinc-800">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-zinc-400 font-mono">{pct}%</span>
    </div>
  );
}

function HostCard({ host }: { host: LiveHost }) {
  const cpuColor = host.cpu > 80 ? 'text-red-400' : host.cpu > 60 ? 'text-orange-400' : 'text-green-400';
  return (
    <div className="flex items-center justify-between bg-zinc-900/60 border border-zinc-800 rounded-xl px-4 py-3">
      <div className="flex items-center gap-3">
        <div className={`flex items-center justify-center w-8 h-8 rounded-lg ${host.is_cloud ? 'bg-blue-500/15' : 'bg-zinc-800'}`}>
          {host.is_cloud ? <Cloud className="w-4 h-4 text-blue-400" /> : <Laptop className="w-4 h-4 text-zinc-400" />}
        </div>
        <div>
          <p className="text-xs font-semibold text-white leading-none">{host.display_label}</p>
          <p className="text-[10px] text-zinc-500 mt-0.5 font-mono">{host.ip_address}</p>
        </div>
      </div>
      <div className="flex items-center gap-4 text-right">
        <div>
          <p className="text-[10px] text-zinc-500">CPU</p>
          <p className={`text-sm font-bold font-mono ${cpuColor}`}>{host.cpu}%</p>
        </div>
        <div>
          <p className="text-[10px] text-zinc-500">RAM</p>
          <p className="text-sm font-bold font-mono text-zinc-300">{host.mem}%</p>
        </div>
        <div className={`w-2 h-2 rounded-full ${host.status === 'online' ? 'bg-green-400' : 'bg-zinc-600'}`} />
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AttackDetectionPage() {
  const [filter, setFilter] = useState<string>('all');

  const { data: incidents = [], isLoading: incLoading, refetch } = useQuery<LiveIncident[]>({
    queryKey: ['incidents'],
    queryFn: async () => {
      try { const r = await api.get('/incidents?limit=80'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 8000,
  });

  const { data: hosts = [] } = useQuery<LiveHost[]>({
    queryKey: ['hosts'],
    queryFn: async () => {
      try { const r = await api.get('/hosts'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 10000,
  });

  const threats = incidents.filter(i => i.tier1_family !== 'benign');
  const awsHosts = hosts.filter(h => h.is_cloud);
  const localHosts = hosts.filter(h => !h.is_cloud);

  const families = Array.from(new Set(threats.map(i => i.tier1_family)));
  const filtered = filter === 'all' ? threats : threats.filter(i => i.tier1_family === filter);

  // Threat-family breakdown counts
  const familyCounts: Record<string, number> = {};
  threats.forEach(t => { familyCounts[t.tier1_family] = (familyCounts[t.tier1_family] ?? 0) + 1; });

  const topFamilies = Object.entries(familyCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const maxCount = topFamilies[0]?.[1] ?? 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            Attack Detection
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            Live threat classification — UNSW-NB15 ground truth &middot; Two-Tier ML engine
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Total Threats', value: threats.length, color: 'text-red-400', icon: <AlertTriangle className="w-4 h-4" /> },
          { label: 'AWS Nodes Online', value: awsHosts.length, color: 'text-blue-400', icon: <Cloud className="w-4 h-4" /> },
          { label: 'Local Nodes', value: localHosts.length, color: 'text-zinc-300', icon: <Laptop className="w-4 h-4" /> },
          { label: 'Awaiting Approval', value: threats.filter(t => t.status === 'awaiting_approval' || t.status === 'ready_for_review').length, color: 'text-amber-400', icon: <Clock className="w-4 h-4" /> },
        ].map(s => (
          <div key={s.label} className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
            <div className={`flex items-center gap-1.5 text-xs font-medium mb-2 ${s.color}`}>
              {s.icon}
              <span>{s.label}</span>
            </div>
            <p className={`text-3xl font-bold font-mono ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Two-column: family breakdown + fleet */}
      <div className="grid grid-cols-5 gap-4">
        {/* Attack family bar chart */}
        <div className="col-span-2 bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
          <h2 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-4">Threat Families Detected</h2>
          <div className="space-y-3">
            {topFamilies.map(([fam, cnt]) => (
              <div key={fam}>
                <div className="flex items-center justify-between mb-1">
                  <FamilyBadge family={fam} />
                  <span className="text-xs font-mono font-bold text-white">{cnt}</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-red-500 to-orange-400"
                    style={{ width: `${(cnt / maxCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
            {topFamilies.length === 0 && (
              <p className="text-xs text-zinc-600 py-4 text-center">No threats detected yet</p>
            )}
          </div>
        </div>

        {/* Live fleet */}
        <div className="col-span-3 bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
          <h2 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Wifi className="w-3.5 h-3.5 text-green-400" />
            Live Fleet — {hosts.length} Nodes
          </h2>
          <div className="space-y-2">
            {hosts.map(h => <HostCard key={h.id} host={h} />)}
            {hosts.length === 0 && (
              <p className="text-xs text-zinc-600 py-4 text-center">Connecting to telemetry hub…</p>
            )}
          </div>
        </div>
      </div>

      {/* Incident table */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-zinc-800">
          <h2 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">
            Detected Attacks ({filtered.length})
          </h2>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setFilter('all')}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${filter === 'all' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'}`}
            >
              All
            </button>
            {families.map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${filter === f ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'}`}
              >
                {FAMILY_LABEL[f] ?? f}
              </button>
            ))}
          </div>
        </div>

        {incLoading ? (
          <div className="py-12 text-center text-xs text-zinc-600">Loading incidents…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500 font-mono uppercase text-[10px]">
                  <th className="px-5 py-2.5 text-left">Attack Family</th>
                  <th className="px-5 py-2.5 text-left">MITRE Technique</th>
                  <th className="px-5 py-2.5 text-left">Host</th>
                  <th className="px-5 py-2.5 text-left">Source</th>
                  <th className="px-5 py-2.5 text-left">Confidence</th>
                  <th className="px-5 py-2.5 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 25).map((inc) => (
                  <tr key={inc.incident_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                    <td className="px-5 py-3">
                      <FamilyBadge family={inc.tier1_family} />
                    </td>
                    <td className="px-5 py-3 font-mono text-zinc-400 text-[10px]">
                      {inc.tier2_technique ?? '—'}
                    </td>
                    <td className="px-5 py-3 text-zinc-300 max-w-[150px] truncate" title={inc.host_id}>
                      {inc.host_id}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`text-[10px] font-mono ${inc.source === 'unsw_nb15_replay' ? 'text-blue-400' : inc.source === 'live_aws' ? 'text-green-400' : 'text-zinc-500'}`}>
                        {inc.source === 'unsw_nb15_replay' ? '📊 UNSW-NB15' : inc.source === 'live_aws' ? '☁️ AWS Live' : inc.source === 'simulated' ? '🖥️ Simulated' : inc.source}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <ConfBar value={inc.tier1_confidence} />
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={inc.status} />
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-10 text-center text-zinc-600">No threats for this filter</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
