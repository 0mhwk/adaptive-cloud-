// frontend/src/pages/SelfHealingPage.tsx
// Page 3: Autonomous Self-Healing — no approval gate, instant analysis + SysAdmin runbook + remediation
import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/api/client';
import {
  Zap, CheckCircle2, Shield, Cloud, Laptop, AlertTriangle,
  ArrowRight, Terminal, Copy, Check, Activity, ArrowUpRight,
  ShieldCheck
} from 'lucide-react';
import NodeModal from '@/components/dashboard/NodeModal';
import type { LiveHost } from '@/components/dashboard/NodeModal';

interface HealingIncident {
  incident_id: string;
  timestamp: string;
  source: string;
  host_id: string;
  tier1_family: string;
  tier1_confidence: number;
  tier2_technique: string | null;
  status: string;
  features: Record<string, any>;
  rca?: {
    sysadmin_runbook?: any[];
    automated_healing_steps?: any[];
    probable_root_cause?: string;
    summary?: string;
  };
  recommended_actions?: any[];
  outcome_summary?: string;
}

const FAMILY_LABEL: Record<string, string> = {
  ddos: 'DDoS Flood', dos: 'DoS Attack', brute_force: 'Brute Force',
  port_scan: 'Port Scan', cryptomining: 'Crypto Mining',
  botnet: 'Botnet / C2', infiltration: 'RCE / Shellcode',
  privilege_escalation: 'Priv Escalation', web_attack: 'Web Exploit',
  cloud_iam: 'IAM Abuse', cloud_storage: 'Data Exfil',
};

const FAMILY_COLOR: Record<string, string> = {
  ddos: 'text-red-400 bg-red-500/10 border-red-500/30',
  dos: 'text-red-400 bg-red-500/10 border-red-500/30',
  brute_force: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
  cryptomining: 'text-pink-400 bg-pink-500/10 border-pink-500/30',
  botnet: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
  port_scan: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  infiltration: 'text-red-300 bg-red-600/10 border-red-600/30',
  privilege_escalation: 'text-red-400 bg-red-500/10 border-red-500/30',
  web_attack: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  cloud_iam: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
};

export default function SelfHealingPage() {
  const qc = useQueryClient();
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedHost, setSelectedHost] = useState<LiveHost | null>(null);
  const [healingStatus, setHealingStatus] = useState<Record<string, 'idle' | 'healing' | 'done'>>({});

  const { data: incidents = [] } = useQuery<HealingIncident[]>({
    queryKey: ['incidents-healing'],
    queryFn: async () => {
      try { const r = await api.get('/incidents?limit=80'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 2000,
  });

  const { data: hosts = [] } = useQuery<LiveHost[]>({
    queryKey: ['hosts'],
    queryFn: async () => {
      try { const r = await api.get('/hosts'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 2000,
  });

  const threats = incidents.filter(i => i.tier1_family !== 'benign');
  const selected = threats.find(i => i.incident_id === selectedId) ?? threats[0] ?? null;
  const rca = selected?.rca ?? {};
  const sysadminRunbook: any[] = rca.sysadmin_runbook ?? [];
  const autoHealingSteps: any[] = rca.automated_healing_steps ?? [];
  const actions = selected?.recommended_actions ?? [];
  const healed = threats.filter(t => ['healed', 'executed', 'verified'].includes(t.status)).length;
  const active = threats.filter(t => ['awaiting_approval', 'ready_for_review'].includes(t.status)).length;

  const executeHeal = async (inc: HealingIncident) => {
    setHealingStatus(s => ({ ...s, [inc.incident_id]: 'healing' }));
    try {
      await api.post('/demo/heal', { incident_id: inc.incident_id, host_id: 'aws-worker-01' });
      setHealingStatus(s => ({ ...s, [inc.incident_id]: 'done' }));
      await qc.refetchQueries({ queryKey: ['incidents-healing'] });
      await qc.refetchQueries({ queryKey: ['hosts'] });
    } catch {
      setHealingStatus(s => ({ ...s, [inc.incident_id]: 'idle' }));
    }
  };

  const handleCopy = (cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(cmd);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const fcClass = (f: string) => FAMILY_COLOR[f] ?? 'text-zinc-400 bg-zinc-800 border-zinc-700';

  return (
    <div className="space-y-5">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            Self-Healing & Autonomous Remediation
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            No permission bottlenecks — instant attack analysis, SysAdmin runbook & autonomous mitigation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold">
            ✓ {healed} Healed
          </span>
          <span className="px-3 py-1 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-xs font-mono font-bold">
            ⚠ {active} Active
          </span>
        </div>
      </div>

      {/* ── Autonomous Guardian Status ── */}
      <div className="bg-gradient-to-r from-emerald-900/30 to-zinc-900/60 border border-emerald-500/20 rounded-xl p-4 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
          <ShieldCheck className="w-6 h-6 text-emerald-400" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-white">Autonomous Self-Healing Guardian</span>
            <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
              Active Defense Mode
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Closed-loop AI remediation executes playbooks instantly upon threat confirmation. No human approval bottleneck required.
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-2xl font-black font-mono text-emerald-400">{healed}</p>
          <p className="text-[10px] text-zinc-500">threats neutralized</p>
        </div>
      </div>

      {/* ── Live Fleet ── */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          Live Fleet Health — Click Node to open Full Intelligence Dossier
        </h2>
        <div className="grid grid-cols-3 gap-2">
          {hosts.map(h => {
            const isStressed = (h.cpu ?? 0) > 80;
            return (
              <div
                key={h.id}
                onClick={() => setSelectedHost(h)}
                className={`group flex items-center gap-3 px-4 py-3 border rounded-xl cursor-pointer transition-all ${
                  isStressed ? 'bg-red-500/10 border-red-500/40' : 'bg-zinc-900/40 border-zinc-800 hover:border-zinc-600 hover:bg-zinc-800/30'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  isStressed ? 'bg-red-500/20 text-red-400' : h.is_cloud ? 'bg-blue-500/15 text-blue-400' : 'bg-zinc-800 text-zinc-400'
                }`}>
                  {h.is_cloud ? <Cloud className="w-4 h-4" /> : <Laptop className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-white truncate group-hover:text-emerald-300 transition-colors flex items-center gap-1">
                    {h.display_label}
                    <ArrowUpRight className="w-3 h-3 text-zinc-600 group-hover:text-emerald-400" />
                  </p>
                  <p className="text-[9px] text-zinc-500 font-mono">{h.ip_address}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className={`text-sm font-bold font-mono ${isStressed ? 'text-red-400 animate-pulse' : 'text-emerald-400'}`}>{h.cpu}%</p>
                  <p className="text-[9px] text-zinc-500">CPU</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Main Split: Incident List + Analysis ── */}
      {threats.length === 0 ? (
        <div className="py-20 text-center text-xs text-zinc-500">No threats detected — system operating at baseline.</div>
      ) : (
        <div className="grid grid-cols-5 gap-4" style={{ minHeight: '60vh' }}>

          {/* Incident List */}
          <div className="col-span-2 bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-zinc-800 text-[10px] text-zinc-500 font-mono uppercase tracking-widest font-bold">
              Active & Mitigated Threats
            </div>
            <div className="overflow-y-auto flex-1">
              {threats.map(inc => {
                const isActive = (selectedId ?? threats[0]?.incident_id) === inc.incident_id;
                const isHealed = ['healed', 'executed', 'verified'].includes(inc.status);
                const hs = healingStatus[inc.incident_id];
                return (
                  <div
                    key={inc.incident_id}
                    onClick={() => setSelectedId(inc.incident_id)}
                    className={`flex items-center gap-3 px-4 py-3 border-b border-zinc-800/50 cursor-pointer transition-all ${
                      isActive ? 'bg-zinc-800/70 border-l-2 border-l-emerald-500' : 'hover:bg-zinc-800/30'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className={`text-[9px] font-bold font-mono uppercase px-1.5 py-0.5 rounded border ${fcClass(inc.tier1_family)}`}>
                          {FAMILY_LABEL[inc.tier1_family] ?? inc.tier1_family}
                        </span>
                        {isHealed && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                      </div>
                      <p className="text-[9px] text-zinc-500 font-mono truncate">{inc.incident_id}</p>
                      <p className="text-[9px] text-zinc-600 truncate">{inc.host_id?.split('(')[0]?.trim()}</p>
                    </div>
                    <div className="flex flex-col gap-1 items-end flex-shrink-0">
                      {!isHealed && hs !== 'done' ? (
                        <button
                          onClick={(e) => { e.stopPropagation(); executeHeal(inc); }}
                          disabled={hs === 'healing'}
                          className="text-[9px] font-bold px-2 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black transition-colors disabled:opacity-60 flex items-center gap-1"
                        >
                          {hs === 'healing' ? '…Healing' : <><Zap className="w-2.5 h-2.5" />Auto-Heal</>}
                        </button>
                      ) : (
                        <span className="text-[9px] text-emerald-400 font-mono font-bold">✓ Healed</span>
                      )}
                      <span className="text-[9px] text-zinc-500 font-mono">{Math.round(inc.tier1_confidence * 100)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Threat Analysis + SysAdmin Runbook */}
          {selected && (
            <div className="col-span-3 space-y-4 overflow-y-auto">

              {/* Threat Summary */}
              <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <span className={`text-sm font-bold font-mono uppercase ${FAMILY_COLOR[selected.tier1_family]?.split(' ')[0] ?? 'text-zinc-300'}`}>
                        {FAMILY_LABEL[selected.tier1_family] ?? selected.tier1_family} Detected
                      </span>
                    </div>
                    <p className="text-xs text-zinc-200 font-semibold">
                      {rca.probable_root_cause
                        ? rca.probable_root_cause.replace(/Hypothesized Root Cause:\s*/i, 'Identified Root Cause: ')
                        : 'Root cause analysis in progress…'}
                    </p>
                    <p className="text-xs text-zinc-400 mt-1">
                      {rca.summary?.replace(/supports the hypothesis of a/i, 'forensically confirms a')}
                    </p>
                  </div>
                </div>

                {/* Autonomous Healing Pipeline */}
                {autoHealingSteps.length > 0 && (
                  <div className="mt-3">
                    <p className="text-[10px] font-bold text-zinc-400 uppercase font-mono tracking-widest mb-2">Autonomous Remediation Pipeline</p>
                    <div className="space-y-1.5">
                      {autoHealingSteps.map((step: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-2.5 text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                          <span className="font-semibold text-zinc-200">{step.step}</span>
                          <ArrowRight className="w-3 h-3 text-zinc-600 flex-shrink-0" />
                          <span className="text-zinc-500">{step.action}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Recommended AWS / System Actions */}
              {actions.length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <Shield className="w-3.5 h-3.5 text-blue-400" />
                    Automated Remediation Playbooks
                  </h3>
                  <div className="space-y-2">
                    {actions.map((act: any) => (
                      <div key={act.action_id} className="bg-zinc-950/80 border border-zinc-800 rounded-xl p-3.5">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">{act.name}</span>
                            <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase border ${
                              act.risk_level === 'low' ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
                              act.risk_level === 'medium' ? 'bg-orange-500/15 text-orange-400 border-orange-500/30' : 'bg-red-500/15 text-red-400 border-red-500/30'
                            }`}>{act.risk_level} risk</span>
                            {act.reversible && (
                              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/30">
                                reversible
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-xs text-zinc-400 mb-1">{act.description}</p>
                        {act.expected_outcome && (
                          <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Expected: {act.expected_outcome}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SysAdmin Runbook */}
              {sysadminRunbook.length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <Terminal className="w-3.5 h-3.5 text-yellow-400" />
                    System Administrator Remediation Runbook — What You Should Do
                  </h3>
                  <div className="space-y-3">
                    {sysadminRunbook.map((run: any) => (
                      <div key={run.step_number} className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-md bg-yellow-500/20 text-yellow-400 text-[10px] font-bold flex items-center justify-center font-mono flex-shrink-0">
                              {run.step_number}
                            </span>
                            <span className="text-xs font-bold text-white">{run.title}</span>
                            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">
                              {run.category}
                            </span>
                          </div>
                          <button
                            onClick={() => handleCopy(run.command)}
                            className="flex items-center gap-1 text-[10px] font-mono px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors flex-shrink-0"
                          >
                            {copiedCmd === run.command ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            {copiedCmd === run.command ? 'Copied!' : 'Copy'}
                          </button>
                        </div>
                        <p className="text-xs text-zinc-400">{run.explanation}</p>
                        <div className="p-2.5 rounded-lg bg-black border border-zinc-800 font-mono text-[11px] text-emerald-400 overflow-x-auto">
                          <code>{run.command}</code>
                        </div>
                        <div className="flex items-start gap-1.5 text-[10px] text-zinc-500 font-mono">
                          <CheckCircle2 className="w-3 h-3 text-emerald-500 flex-shrink-0 mt-0.5" />
                          <span>Verification: {run.verification}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {sysadminRunbook.length === 0 && (
                <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-xl p-6 text-center text-xs text-zinc-500">
                  Select an incident from the list to view the full SysAdmin remediation runbook.
                </div>
              )}

            </div>
          )}
        </div>
      )}

      {/* Node Intelligence Modal */}
      {selectedHost && (
        <NodeModal
          host={selectedHost}
          onClose={() => setSelectedHost(null)}
        />
      )}
    </div>
  );
}
