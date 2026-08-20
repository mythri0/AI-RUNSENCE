import { type Metrics } from '../api/client'

interface Props { metrics: Metrics }

const METRIC_DEFS: { key: keyof Metrics; label: string; icon: string; desc: string; good?: string }[] = [
  { key: 'cadence', label: 'Cadence', icon: '🦶', desc: 'Steps per minute', good: '170–185 SPM' },
  { key: 'symmetry_index', label: 'Symmetry Index', icon: '⚖️', desc: 'Left-right balance (0–100)', good: '80–100' },
  { key: 'vertical_oscillation', label: 'Vertical Oscillation', icon: '↕️', desc: 'Normalized bounce (lower = better)', good: '< 0.05' },
  { key: 'trunk_lean', label: 'Trunk Lean', icon: '🏗', desc: 'Forward lean angle', good: '5–12°' },
  { key: 'arm_swing', label: 'Arm Swing', icon: '💪', desc: 'Mean elbow angle', good: '80–100°' },
  { key: 'pelvic_stability', label: 'Pelvic Stability', icon: '🔩', desc: 'Hip stability score (0–100)', good: '> 75' },
  { key: 'rhythm_score', label: 'Rhythm Score', icon: '🥁', desc: 'Stride consistency (0–100)', good: '> 75' },
  { key: 'stride_normalized', label: 'Stride Length', icon: '📏', desc: 'Normalized stride (relative to image)', good: 'Context-dependent' },
  { key: 'ground_contact_estimate', label: 'Ground Contact', icon: '🦶', desc: 'Estimated contact ratio (0–1)', good: '< 0.35' },
  { key: 'knee_angle_left', label: 'Knee Flex (Left)', icon: '🦵', desc: 'Peak knee angle at mid-swing', good: '> 60°' },
  { key: 'knee_angle_right', label: 'Knee Flex (Right)', icon: '🦵', desc: 'Peak knee angle at mid-swing', good: '> 60°' },
]

export default function MetricsGrid({ metrics }: Props) {
  if (!metrics) return <p style={{ color: 'var(--text-secondary)' }}>No metrics available yet.</p>

  // Foot strike special
  const fs = metrics.foot_strike

  return (
    <div>
      {fs && (
        <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.25rem', borderColor: 'var(--accent-teal-border)', background: 'var(--accent-teal-bg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <p style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--accent-teal-dark)', marginBottom: '0.25rem' }}>
                🦶 Foot Strike Pattern
              </p>
              <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-teal-dark)' }}>{fs.label ?? fs.classification ?? '—'}</p>
              {fs.note && <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{fs.note}</p>}
            </div>
            {fs.confidence != null && (
              <ConfidenceBadge confidence={fs.confidence} />
            )}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '0.9rem' }}>
        {METRIC_DEFS.map(def => {
          const m = metrics[def.key] as { value?: number | null; estimated?: boolean; confidence?: number; note?: string } | null | undefined
          if (!m) return null
          return (
            <div key={def.key} className="metric-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <p style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
                  {def.icon} {def.label}
                </p>
                {m.confidence != null && <ConfidenceBadge confidence={m.confidence} />}
              </div>
              <p style={{ fontSize: '1.6rem', fontWeight: 800, lineHeight: 1, color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
                {m.value != null ? formatValue(m.value, def.key) : <span style={{ color: 'var(--text-muted)' }}>N/A</span>}
              </p>
              {m.estimated && (
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>⚠️ estimated</p>
              )}
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{def.desc}</p>
              {def.good && (
                <p style={{ fontSize: '0.72rem', color: 'var(--accent-teal)', marginTop: '0.3rem', fontWeight: 600 }}>Target: {def.good}</p>
              )}
              {m.note && (
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem', fontStyle: 'italic' }}>{m.note}</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function formatValue(v: number, key: string): string {
  if (key === 'cadence') return `${v.toFixed(0)} SPM`
  if (key.includes('angle') || key === 'trunk_lean') return `${v.toFixed(1)}°`
  if (key === 'vertical_oscillation') return `${v.toFixed(3)}`
  if (key === 'stride_normalized') return `${v.toFixed(2)}x`
  if (key === 'ground_contact_estimate') return `${(v * 100).toFixed(0)}%`
  if (key.includes('score') || key.includes('index') || key.includes('stability')) return `${v.toFixed(0)}/100`
  return `${v.toFixed(1)}`
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const isHigh = pct >= 75
  const isMed = pct >= 50
  return (
    <span style={{
      fontSize: '0.7rem',
      fontWeight: 600,
      padding: '0.15rem 0.5rem',
      borderRadius: '20px',
      background: isHigh ? 'rgba(5,150,105,0.08)' : isMed ? 'var(--accent-orange-bg)' : 'rgba(220,38,38,0.08)',
      color: isHigh ? '#059669' : isMed ? '#d97706' : '#dc2626',
      border: `1px solid ${isHigh ? 'rgba(5,150,105,0.2)' : isMed ? 'rgba(245,158,11,0.25)' : 'rgba(220,38,38,0.2)'}`,
    }}>
      {pct}% conf
    </span>
  )
}
