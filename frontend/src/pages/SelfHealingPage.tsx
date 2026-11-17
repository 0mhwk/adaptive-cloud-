// frontend/src/pages/SelfHealingPage.tsx
// Page 3: Self-Healing System — approval gate, playbooks, AWS actions
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/api/client';
import { Zap, CheckCircle2, XCircle, Clock, Shield, RotateCcw, AlertTriangle } from 'lucide-react';

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
  self_healing?: {
    playbook_id?: string;
    playbook_name?: string;
    risk_level?: string;
    reversible?: boolean;
    target_layer?: string;
    status?: string;
  };
  recommended_actions?: Array<{
    action_id?: string;
    name?: string;
    description?: string;
    risk_level?: string;
    reversible?: boolean;
    expected_outcome?: string;
    rollback_steps?: string;
  }>;
  approval?: {
    decided_by?: string | null;
    decision?: string | null;
    decided_at?: string | null;
    comment?: string | null;
  };
  outcome_summary?: string;
}

const PLAYBOOK_ICON: Record<string, string> = {
  ACT_AWS_SG_BLOCK: '🛡️',
  ACT_AWS_WAF_RATE_LIMIT: '⚡',
  ACT_AWS_DEACTIVATE_IAM_KEY: '🔑',
  ACT_BLOCK_SOURCE_IP: '🚫',
  ACT_ISOLATE_HOST: '🔒',
  ACT_KILL_PROCESS: '☠️',
};

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  awaiting_approval: { label: 'Awaiting Approval', color: 'text-amber-400', bg: 'bg-amber-500/15 border-amber-500/30' },
  ready_for_review: { label: 'Ready for Review', color: 'text-blue-400', bg: 'bg-blue-500/15 border-blue-500/30' },
  approved: { label: 'Approved', color: 'text-green-400', bg: 'bg-green-500/15 border-green-500/30' },
  executed: { label: 'Executed', color: 'text-emerald-400', bg: 'bg-emerald-500/15 border-emerald-500/30' },
  rejected: { label: 'Rejected', color: 'text-zinc-400', bg: 'bg-zinc-700/40 border-zinc-700' },
  recorded: { label: 'Archived', color: 'text-zinc-500', bg: 'bg-zinc-800/60 border-zinc-700' },
  healed: { label: 'Healed ✓', color: 'text-green-300', bg: 'bg-green-600/15 border-green-600/30' },
};

function RiskBadge({ level }: { level?: string }) {
  const map: Record<string, string> = {
    high: 'bg-red-500/20 text-red-400',
    medium: 'bg-orange-500/20 text-orange-400',
    low: 'bg-green-500/20 text-green-400',
  };
  return (
    <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${map[level ?? 'low'] ?? map.low}`}>
      {level ?? 'low'} risk
    </span>
  );
}

export default function SelfHealingPage() {
  const qc = useQueryClient();
  const [approving, setApproving] = useState<string | null>(null);
  const [operator] = useState('SOC-Engineer');

  const { data: incidents = [], isLoading } = useQuery<HealingIncident[]>({
    queryKey: ['incidents-healing'],
    queryFn: async () => {
      try { const r = await api.get('/incidents?limit=80'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 8000,
  });

  const approveMut = useMutation({
    mutationFn: async ({ id, comment }: { id: string; comment: string }) => {
      const r = await api.post(`/incidents/${id}/approve`, {
        decided_by: operator,
        comment,
        dry_run: false,
      });
      return r.data;
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['incidents-healing'] }); setApproving(null); },
  });

  const rejectMut = useMutation({
    mutationFn: async (id: string) => {
      const r = await api.post(`/incidents/${id}/reject`, {
        decided_by: operator,
        comment: 'Rejected by operator after review.',
      });
      return r.data;
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['incidents-healing'] }); },
  });

  const threats = incidents.filter(i => i.tier1_family !== 'benign');
  const pending = threats.filter(i => i.status === 'awaiting_approval' || i.status === 'ready_for_review');
  const approved = threats.filter(i => i.status === 'approved' || i.status === 'executed' || i.status === 'healed');
  const rejected = threats.filter(i => i.status === 'rejected');
  const archived = threats.filter(i => i.status === 'recorded');

  // Count by playbook
  const playbookCounts: Record<string, number> = {};
  threats.forEach(t => {
    const pb = t.self_healing?.playbook_id ?? 'Unknown';
    playbookCounts[pb] = (playbookCounts[pb] ?? 0) + 1;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          Self-Healing System
        </h1>
        <p className="text-xs text-zinc-500 mt-0.5">
          Human-in-the-loop approval gate — zero autonomous execution without SOC approval
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Pending Approval', value: pending.length, color: 'text-amber-400', icon: <Clock className="w-4 h-4" /> },
          { label: 'Approved & Healed', value: approved.length, color: 'text-green-400', icon: <CheckCircle2 className="w-4 h-4" /> },
          { label: 'Rejected', value: rejected.length, color: 'text-zinc-400', icon: <XCircle className="w-4 h-4" /> },
          { label: 'Dataset Archived', value: archived.length, color: 'text-blue-400', icon: <Shield className="w-4 h-4" /> },
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

      {/* Playbook usage */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-4">Playbooks Recommended</h2>
        <div className="flex flex-wrap gap-3">
          {Object.entries(playbookCounts).map(([pb, cnt]) => (
            <div key={pb} className="flex items-center gap-2 bg-zinc-800/60 border border-zinc-700 rounded-lg px-3 py-2">
              <span className="text-sm">{PLAYBOOK_ICON[pb] ?? '📋'}</span>
              <div>
                <p className="text-[10px] font-mono text-zinc-300">{pb}</p>
                <p className="text-xs font-bold text-white">{cnt}×</p>
              </div>
            </div>
          ))}
          {Object.keys(playbookCounts).length === 0 && (
            <p className="text-xs text-zinc-600">No playbooks generated yet</p>
          )}
        </div>
      </div>

      {/* Approval gate — pending incidents */}
      {pending.length > 0 && (
        <div className="bg-zinc-900/60 border border-amber-500/20 rounded-xl overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-3.5 border-b border-zinc-800 bg-amber-500/5">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h2 className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              {pending.length} Pending — Awaiting SOC Approval
            </h2>
          </div>
          <div className="divide-y divide-zinc-800/50">
            {pending.map(inc => {
              const sh = inc.self_healing ?? {};
              const actions = inc.recommended_actions ?? [];
              const isApproving = approving === inc.incident_id;
              return (
                <div key={inc.incident_id} className="px-5 py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <span className="text-[10px] font-bold font-mono text-amber-400 uppercase">
                          {inc.tier1_family.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[10px] font-mono text-zinc-500">{inc.incident_id}</span>
                        <RiskBadge level={sh.risk_level} />
                        {sh.reversible && (
                          <span className="flex items-center gap-1 text-[10px] text-green-400">
                            <RotateCcw className="w-2.5 h-2.5" /> Reversible
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-zinc-400 truncate mb-1">Host: {inc.host_id}</p>
                      <p className="text-xs text-zinc-300 font-semibold">{sh.playbook_name ?? sh.playbook_id ?? 'No playbook'}</p>
                      {actions[0] && (
                        <p className="text-[10px] text-zinc-500 mt-1">{actions[0].description ?? actions[0].expected_outcome}</p>
                      )}
                    </div>

                    {!isApproving ? (
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={() => setApproving(inc.incident_id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/15 border border-green-500/30 text-green-400 text-xs font-bold hover:bg-green-500/25 transition-colors"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                        </button>
                        <button
                          onClick={() => rejectMut.mutate(inc.incident_id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 text-xs font-bold hover:text-white transition-colors"
                        >
                          <XCircle className="w-3.5 h-3.5" /> Reject
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={() => approveMut.mutate({ id: inc.incident_id, comment: 'Approved after SOC review.' })}
                          disabled={approveMut.isPending}
                          className="px-3 py-1.5 rounded-lg bg-green-500 text-black text-xs font-bold hover:bg-green-400 transition-colors disabled:opacity-50"
                        >
                          {approveMut.isPending ? 'Executing…' : 'Confirm Execute'}
                        </button>
                        <button onClick={() => setApproving(null)} className="text-xs text-zinc-500 hover:text-white transition-colors">
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* All incidents table (compact) */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-zinc-800">
          <h2 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">All Healing Records</h2>
        </div>
        {isLoading ? (
          <div className="py-10 text-center text-xs text-zinc-600">Loading…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500 font-mono uppercase text-[10px]">
                  <th className="px-5 py-2.5 text-left">Attack Family</th>
                  <th className="px-5 py-2.5 text-left">Playbook</th>
                  <th className="px-5 py-2.5 text-left">Risk</th>
                  <th className="px-5 py-2.5 text-left">Status</th>
                  <th className="px-5 py-2.5 text-left">Decided By</th>
                </tr>
              </thead>
              <tbody>
                {threats.slice(0, 30).map(inc => {
                  const sh = inc.self_healing ?? {};
                  const sc = STATUS_CONFIG[inc.status] ?? { label: inc.status, color: 'text-zinc-400', bg: '' };
                  return (
                    <tr key={inc.incident_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                      <td className="px-5 py-2.5 font-mono font-bold text-zinc-300 uppercase text-[10px]">
                        {inc.tier1_family.replace(/_/g, ' ')}
                      </td>
                      <td className="px-5 py-2.5 text-zinc-400">
                        {PLAYBOOK_ICON[sh.playbook_id ?? ''] ?? '📋'} {sh.playbook_id ?? '—'}
                      </td>
                      <td className="px-5 py-2.5">
                        <RiskBadge level={sh.risk_level} />
                      </td>
                      <td className="px-5 py-2.5">
                        <span className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full border ${sc.bg} ${sc.color}`}>
                          {sc.label}
                        </span>
                      </td>
                      <td className="px-5 py-2.5 text-zinc-500 font-mono text-[10px]">
                        {inc.approval?.decided_by ?? '—'}
                      </td>
                    </tr>
                  );
                })}
                {threats.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-5 py-10 text-center text-zinc-600">No records yet</td>
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
