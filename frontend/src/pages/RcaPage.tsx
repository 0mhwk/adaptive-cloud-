// frontend/src/pages/RCAPage.tsx
// Page 2: Root Cause Analysis — shows selected incident's full forensic breakdown
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/api/client';
import { Search, ChevronRight, AlertCircle, CheckCircle2, Info } from 'lucide-react';

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
    primary_telemetry_signal?: string;
    evidence?: Record<string, any>;
    confidence?: number;
    alternative_hypotheses?: string[];
    uncertainty_note?: string;
  };
  recommended_actions?: Array<{
    action_id?: string;
    name?: string;
    description?: string;
    risk_level?: string;
    reversible?: boolean;
    expected_outcome?: string;
  }>;
}

const FAMILY_COLOR: Record<string, string> = {
  ddos: 'text-red-400', dos: 'text-red-400', brute_force: 'text-orange-400',
  port_scan: 'text-yellow-400', port_scan_recon: 'text-yellow-400',
  web_attack: 'text-purple-400', cryptomining: 'text-pink-400',
  botnet: 'text-rose-400', infiltration: 'text-red-300',
  exploit_other: 'text-orange-300', privilege_escalation: 'text-red-400',
};

function FeatureRow({ label, value, unit = '' }: { label: string; value: number | string; unit?: string }) {
  const v = typeof value === 'number' ? value : parseFloat(String(value));
  const isHigh = typeof v === 'number' && !isNaN(v) && v > 70;
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-zinc-800/50 last:border-0">
      <span className="text-xs text-zinc-500">{label}</span>
      <span className={`text-xs font-mono font-bold ${isHigh ? 'text-red-400' : 'text-zinc-200'}`}>
        {typeof v === 'number' && !isNaN(v) ? v.toFixed(1) : String(value)}{unit}
      </span>
    </div>
  );
}

export default function RCAPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: incidents = [], isLoading } = useQuery<LiveIncident[]>({
    queryKey: ['incidents-rca'],
    queryFn: async () => {
      try { const r = await api.get('/incidents?limit=60'); return r.data; }
      catch { return []; }
    },
    refetchInterval: 10000,
  });

  const threats = incidents.filter(i => i.tier1_family !== 'benign');
  const selected = threats.find(i => i.incident_id === selectedId) ?? threats[0] ?? null;

  if (!selectedId && threats.length > 0 && !selectedId) {
    // auto-select first on load
  }

  const rca = selected?.rca ?? {};
  const evidence = rca.evidence ?? {};
  const features = selected?.features ?? {};
  const actions = selected?.recommended_actions ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Search className="w-5 h-5 text-blue-400" />
          Root Cause Analysis
        </h1>
        <p className="text-xs text-zinc-500 mt-0.5">
          Evidence-based forensic analysis — multiplier-calibrated confidence scores
        </p>
      </div>

      <div className="grid grid-cols-5 gap-4" style={{ minHeight: '70vh' }}>
        {/* Incident list panel */}
        <div className="col-span-2 bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-zinc-800 text-[10px] text-zinc-500 font-mono uppercase tracking-wider font-bold">
            {threats.length} threats — click to inspect
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-zinc-800/50">
            {isLoading && (
              <div className="py-8 text-center text-xs text-zinc-600">Loading…</div>
            )}
            {threats.map(inc => (
              <button
                key={inc.incident_id}
                onClick={() => setSelectedId(inc.incident_id)}
                className={`w-full text-left px-4 py-3 transition-all hover:bg-zinc-800/50 ${
                  (selected?.incident_id === inc.incident_id) ? 'bg-zinc-800/70 border-l-2 border-blue-400' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-bold font-mono uppercase ${FAMILY_COLOR[inc.tier1_family] ?? 'text-zinc-400'}`}>
                    {inc.tier1_family.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[10px] text-zinc-600 font-mono">
                    {Math.round(inc.tier1_confidence * 100)}%
                  </span>
                </div>
                <p className="text-xs text-zinc-400 truncate">{inc.host_id}</p>
                <p className="text-[10px] text-zinc-600 font-mono mt-0.5 truncate">{inc.incident_id}</p>
              </button>
            ))}
            {!isLoading && threats.length === 0 && (
              <div className="py-8 text-center text-xs text-zinc-600">No threats detected yet</div>
            )}
          </div>
        </div>

        {/* Detail panel */}
        <div className="col-span-3 space-y-4">
          {!selected ? (
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl flex items-center justify-center h-64 text-zinc-600 text-xs">
              Select an incident to view RCA
            </div>
          ) : (
            <>
              {/* Title card */}
              <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span className={`text-sm font-bold ${FAMILY_COLOR[selected.tier1_family] ?? 'text-white'}`}>
                    {selected.tier1_family.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} Detected
                  </span>
                  <span className="ml-auto text-[10px] font-mono text-zinc-500">{selected.incident_id}</span>
                </div>

                {/* Probable Root Cause */}
                <div className="bg-zinc-800/60 border border-zinc-700/50 rounded-lg p-3 mb-3">
                  <p className="text-[10px] text-zinc-500 font-mono uppercase font-bold mb-1">Probable Root Cause</p>
                  <p className="text-xs text-zinc-200 leading-relaxed">
                    {rca.probable_root_cause ?? rca.summary ?? 'RCA in progress…'}
                  </p>
                </div>

                {/* Telemetry signal */}
                {rca.primary_telemetry_signal && (
                  <div className="flex items-start gap-2 text-xs text-zinc-400 bg-zinc-800/40 rounded-lg p-2.5">
                    <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-blue-400" />
                    <span>{rca.primary_telemetry_signal}</span>
                  </div>
                )}
              </div>

              {/* Features + Evidence side by side */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
                  <p className="text-[10px] font-bold font-mono uppercase text-zinc-500 mb-3">Telemetry Vector</p>
                  <FeatureRow label="CPU Usage" value={features.cpu ?? 0} unit="%" />
                  <FeatureRow label="RAM Usage" value={features.ram ?? 0} unit="%" />
                  <FeatureRow label="Failed Logins" value={features.failed_logins ?? 0} />
                  <FeatureRow label="Inbound Traffic" value={features.inbound_traffic ?? 0} unit=" pps" />
                  <FeatureRow label="Active Conns" value={features.active_connections ?? 0} />
                </div>
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
                  <p className="text-[10px] font-bold font-mono uppercase text-zinc-500 mb-3">Evidence Scores</p>
                  {Object.entries(evidence).slice(0, 5).map(([k, v]) => (
                    <FeatureRow key={k} label={k.replace(/_/g, ' ')} value={typeof v === 'number' ? `${(v * 100).toFixed(0)}%` : String(v)} />
                  ))}
                  {Object.keys(evidence).length === 0 && (
                    <p className="text-xs text-zinc-600 py-2">No evidence scores available</p>
                  )}
                </div>
              </div>

              {/* MITRE technique */}
              <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
                <p className="text-[10px] font-bold font-mono uppercase text-zinc-500 mb-3">MITRE ATT&CK Mapping</p>
                <div className="flex items-center gap-3">
                  <div className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 font-mono text-xs text-blue-400 font-bold">
                    {selected.tier2_technique ?? 'N/A'}
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                    <ChevronRight className="w-3 h-3" />
                    Tier 2 Confidence: <span className="text-white font-bold ml-1">{selected.tier2_confidence ? `${Math.round(selected.tier2_confidence * 100)}%` : '—'}</span>
                  </div>
                </div>
              </div>

              {/* Alternative hypotheses */}
              {rca.alternative_hypotheses && rca.alternative_hypotheses.length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
                  <p className="text-[10px] font-bold font-mono uppercase text-zinc-500 mb-2">Alternative Hypotheses</p>
                  <ul className="space-y-1">
                    {rca.alternative_hypotheses.map((h, i) => (
                      <li key={i} className="text-xs text-zinc-400 flex items-start gap-2">
                        <span className="text-zinc-600 mt-0.5">·</span> {h}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommended Actions */}
              {actions.length > 0 && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
                  <p className="text-[10px] font-bold font-mono uppercase text-zinc-500 mb-3">Recommended Healing Actions</p>
                  <div className="space-y-2">
                    {actions.slice(0, 3).map((a, i) => (
                      <div key={i} className="flex items-start gap-3 bg-zinc-800/50 rounded-lg p-3">
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-semibold text-white">{a.name ?? a.action_id}</p>
                          <p className="text-[10px] text-zinc-500 mt-0.5">{a.description ?? a.expected_outcome}</p>
                          <span className={`inline-block mt-1 text-[10px] font-mono px-1.5 py-0.5 rounded ${a.risk_level === 'high' ? 'bg-red-500/20 text-red-400' : a.risk_level === 'medium' ? 'bg-orange-500/20 text-orange-400' : 'bg-green-500/20 text-green-400'}`}>
                            {a.risk_level} risk · {a.reversible ? 'reversible' : 'irreversible'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
