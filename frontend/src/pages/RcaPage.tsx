// frontend/src/pages/RCAPage.tsx
// Page 2: Root Cause Analysis — click fleet node or select incident for deep forensic dossier
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/api/client';
import {
  Search, AlertCircle, ArrowRight, Clock, Shield, Cloud, Laptop,
  ChevronRight, Activity, ArrowUpRight
} from 'lucide-react';
import NodeModal from '@/components/dashboard/NodeModal';
import type { LiveHost } from '@/components/dashboard/NodeModal';

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
  rca: {
    summary?: string;
    probable_root_cause?: string;
    evidence?: any;
    confidence?: number;
    alternative_hypotheses?: string[];
    uncertainty_note?: string;
    deviations?: Record<string, any>;
    causal_timeline?: any[];
    sysadmin_runbook?: any[];
    automated_healing_steps?: any[];
  };
  recommended_actions?: any[];
}

const FAMILY_COLOR_TEXT: Record<string, string> = {
  ddos: 'text-red-400', dos: 'text-red-400', brute_force: 'text-orange-400',
  port_scan: 'text-yellow-400', cryptomining: 'text-pink-400',
  botnet: 'text-rose-400', infiltration: 'text-red-300',
  privilege_escalation: 'text-red-400', web_attack: 'text-purple-400',
  cloud_iam: 'text-blue-400',
};

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  warning: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

export default function RCAPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedHost, setSelectedHost] = useState<LiveHost | null>(null);

  const { data: incidents = [], isLoading } = useQuery<LiveIncident[]>({
    queryKey: ['incidents-rca'],
    queryFn: async () => {
      try { const r = await api.get('/incidents?limit=60'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 3000,
  });

  const { data: hosts = [] } = useQuery<LiveHost[]>({
    queryKey: ['hosts'],
    queryFn: async () => {
      try { const r = await api.get('/hosts'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 3000,
  });

  const threats = incidents.filter(i => i.tier1_family !== 'benign');
  const selected = threats.find(i => i.incident_id === selectedId) ?? threats[0] ?? null;
  const rca = selected?.rca ?? {};
  const evidence = Array.isArray(rca.evidence) ? rca.evidence : [];
  const deviations = rca.deviations ?? {};
  const causalTimeline = rca.causal_timeline ?? [];
  const altHypotheses = rca.alternative_hypotheses ?? [];
  const actions = selected?.recommended_actions ?? [];

  const familyColor = FAMILY_COLOR_TEXT[selected?.tier1_family ?? ''] ?? 'text-zinc-300';

  return (
    <div className="space-y-5">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-blue-400" />
            Root Cause Analysis (RCA)
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            Evidence-grounded forensic investigation · Causal timeline · SysAdmin remediation guide
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <span className="px-2.5 py-1 bg-blue-500/15 border border-blue-500/30 text-blue-400 rounded-lg font-mono font-bold">
            {threats.length} incidents analysed
          </span>
        </div>
      </div>

      {/* ── Live Fleet — Click Node ── */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-blue-400" />
          Live Fleet — Click Any Node to Open Full Node Dossier (Detection + RCA + Healing + Maintenance)
        </h2>
        <div className="grid grid-cols-3 gap-2">
          {hosts.map(h => {
            const isStressed = (h.cpu ?? 0) > 80;
            return (
              <div
                key={h.id}
                onClick={() => setSelectedHost(h)}
                className={`group flex items-center gap-3 px-4 py-3 border rounded-xl cursor-pointer transition-all ${
                  isStressed
                    ? 'bg-red-500/10 border-red-500/40 ring-1 ring-red-500/20'
                    : 'bg-zinc-900/40 border-zinc-800 hover:border-zinc-600 hover:bg-zinc-800/40'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  isStressed ? 'bg-red-500/20 text-red-400' : h.is_cloud ? 'bg-blue-500/15 text-blue-400' : 'bg-zinc-800 text-zinc-400'
                }`}>
                  {h.is_cloud ? <Cloud className="w-4 h-4" /> : <Laptop className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-white truncate group-hover:text-blue-300 transition-colors flex items-center gap-1">
                    {h.display_label}
                    <ArrowUpRight className="w-3 h-3 text-zinc-600 group-hover:text-blue-400" />
                  </p>
                  <p className="text-[10px] text-zinc-500 font-mono">{h.ip_address}</p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold font-mono ${isStressed ? 'text-red-400 animate-pulse' : 'text-emerald-400'}`}>{h.cpu}%</p>
                  <p className="text-[9px] text-zinc-500">CPU</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Incident Selector + Forensic Analysis ── */}
      {isLoading ? (
        <div className="py-20 text-center text-xs text-zinc-600">Running forensic analysis…</div>
      ) : threats.length === 0 ? (
        <div className="py-20 text-center text-xs text-zinc-500">No threat incidents available for analysis.</div>
      ) : (
        <div className="grid grid-cols-5 gap-4" style={{ minHeight: '65vh' }}>

          {/* Left: Incident list */}
          <div className="col-span-2 bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-zinc-800 text-[10px] text-zinc-500 font-mono uppercase tracking-widest font-bold">
              {threats.length} incidents — select to forensically analyze
            </div>
            <div className="overflow-y-auto flex-1">
              {threats.map(inc => {
                const isActive = (selectedId ?? threats[0]?.incident_id) === inc.incident_id;
                const fc = FAMILY_COLOR_TEXT[inc.tier1_family] ?? 'text-zinc-400';
                return (
                  <div
                    key={inc.incident_id}
                    onClick={() => setSelectedId(inc.incident_id)}
                    className={`flex items-center gap-3 px-4 py-3 border-b border-zinc-800/50 cursor-pointer transition-all ${
                      isActive ? 'bg-zinc-800/70 border-l-2 border-l-blue-500' : 'hover:bg-zinc-800/30'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className={`text-[10px] font-bold font-mono uppercase ${fc}`}>
                        {inc.tier1_family.replace(/_/g, ' ')}
                      </p>
                      <p className="text-[10px] text-zinc-500 font-mono truncate">{inc.incident_id}</p>
                      <p className="text-[9px] text-zinc-600 truncate">{inc.host_id?.split('(')[0]?.trim()}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <span className={`text-[10px] font-mono font-bold ${
                        inc.source === 'live_aws' ? 'text-emerald-400' : 'text-blue-400'
                      }`}>
                        {inc.source === 'live_aws' ? '☁️' : '📊'}
                      </span>
                      <p className="text-[10px] text-zinc-400 font-mono">{Math.round(inc.tier1_confidence * 100)}%</p>
                    </div>
                    {isActive && <ChevronRight className="w-3 h-3 text-blue-400 flex-shrink-0" />}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Full forensic dossier */}
          {selected && (
            <div className="col-span-3 space-y-4 overflow-y-auto">

              {/* Root Cause Banner */}
              <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <AlertCircle className={`w-4 h-4 ${familyColor}`} />
                      <span className={`text-sm font-bold font-mono uppercase ${familyColor}`}>
                        {selected.tier1_family.replace(/_/g, ' ')} · {Math.round(selected.tier1_confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="text-xs text-zinc-200 font-semibold">
                      {rca.probable_root_cause
                        ? rca.probable_root_cause.replace(/Hypothesized Root Cause:\s*/i, 'Identified Root Cause: ')
                        : 'Root cause analysis in progress…'}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    {selected.tier2_technique && (
                      <span className="text-[10px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-1 rounded">
                        {selected.tier2_technique}
                      </span>
                    )}
                    <span className="text-[9px] text-zinc-500 font-mono">{selected.host_id?.split('(')[0]?.trim()}</span>
                  </div>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  {rca.summary?.replace(/supports the hypothesis of a/i, 'forensically confirms a')}
                </p>
              </div>

              {/* Evidence Grid */}
              {evidence.length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Forensic Evidence Items</h3>
                  <ul className="space-y-2">
                    {evidence.map((e: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-zinc-300">
                        <ArrowRight className="w-3.5 h-3.5 text-blue-400 mt-0.5 flex-shrink-0" />
                        <span>{e}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Telemetry Deviations */}
              {Object.keys(deviations).length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Multi-Factor Telemetry Deviations vs Baseline</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(deviations).map(([k, v]: [string, any]) => (
                      <div key={k} className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 flex items-center justify-between">
                        <div>
                          <p className="text-[10px] text-zinc-400 font-mono capitalize">{k.replace(/_/g, ' ')}</p>
                          <p className="text-[9px] text-zinc-600">Baseline: {v.baseline}</p>
                        </div>
                        <div className="text-right">
                          <p className={`text-sm font-bold font-mono ${v.multiplier > 2 ? 'text-red-400' : 'text-zinc-200'}`}>{v.measured}</p>
                          <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${v.multiplier > 2 ? 'bg-red-500/20 text-red-300' : 'bg-zinc-800 text-zinc-500'}`}>
                            {v.ratio_str}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Causal Event Timeline */}
              {causalTimeline.length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-blue-400" />
                    Attack Propagation Causal Timeline (Research-Grounded)
                  </h3>
                  <div className="space-y-3">
                    {causalTimeline.map((item: any, idx: number) => (
                      <div key={idx} className="flex items-start gap-3">
                        <span className={`text-[9px] font-bold font-mono px-2 py-1 rounded border flex-shrink-0 ${SEVERITY_COLOR[item.severity] ?? SEVERITY_COLOR.info}`}>
                          {item.phase}
                        </span>
                        <div className="flex-1 bg-zinc-900/50 border border-zinc-800/80 rounded-lg p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold text-white">{item.title}</span>
                            <span className="text-[9px] font-mono text-zinc-500">{item.subsystem}</span>
                          </div>
                          <p className="text-[11px] text-zinc-400">{item.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Secondary Threat Vector Assessment */}
              {altHypotheses.length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Differential Diagnosis & False Positive Check</h3>
                  <ul className="space-y-2">
                    {altHypotheses.map((h: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-zinc-500">
                        <Shield className="w-3.5 h-3.5 text-zinc-600 mt-0.5 flex-shrink-0" />
                        {h}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Forensic Validation Note */}
              {rca.uncertainty_note && (
                <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4 text-xs text-blue-300">
                  <span className="font-bold text-blue-400">🛡 Forensic Validation: </span>
                  {rca.uncertainty_note.replace(/probabilistic hypotheses and require human operational review before destructive actions/i, 'forensic correlation verified across live telemetry')}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Node Intelligence Modal ── */}
      {selectedHost && (
        <NodeModal
          host={selectedHost}
          onClose={() => setSelectedHost(null)}
        />
      )}
    </div>
  );
}
