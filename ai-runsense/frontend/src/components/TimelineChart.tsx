import { type TimelinePoint, type FatigueReport } from '../api/client'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface Props { points: TimelinePoint[]; fatigue: FatigueReport }

const QUALITY_SCORES: Record<string, number> = { good: 100, fair: 70, poor: 45, degrading: 20 }
const QUALITY_COLORS: Record<string, string> = { good: '#059669', fair: '#d97706', poor: '#ea580c', degrading: '#dc2626' }

export default function TimelineChart({ points, fatigue }: Props) {
  if (!points || points.length === 0) {
    return <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No timeline data available.</div>
  }

  const chartData = points.map(p => ({
    name: `${Math.round(p.time_pct)}%`,
    time_s: p.timestamp_s?.toFixed(1),
    form_quality: QUALITY_SCORES[p.form_quality] ?? 50,
    quality_label: p.form_quality,
    notes: p.notes.join(', '),
    is_baseline: p.is_baseline,
  }))

  const onsetPct = fatigue?.onset_time_s != null && points.length > 0
    ? (fatigue.onset_time_s / (points[points.length - 1]?.timestamp_s || 1)) * 100
    : null

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { payload: typeof chartData[0] }[] }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
      <div style={{ background: '#ffffff', border: '1px solid var(--border)', borderRadius: '10px', padding: '0.75rem 1rem', fontSize: '0.82rem', maxWidth: '240px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
        <p style={{ fontWeight: 700, color: QUALITY_COLORS[d.quality_label], textTransform: 'capitalize', marginBottom: '0.25rem' }}>{d.quality_label}</p>
        <p style={{ color: 'var(--text-secondary)' }}>Position: {d.name} of run</p>
        {d.time_s && <p style={{ color: 'var(--text-secondary)' }}>Time: {d.time_s}s</p>}
        {d.is_baseline && <p style={{ color: 'var(--accent-teal)' }}>📐 Baseline window</p>}
        {d.notes && <p style={{ color: 'var(--text-muted)', marginTop: '0.25rem' }}>{d.notes}</p>}
      </div>
    )
  }

  return (
    <div>
      <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Form Quality Over Time
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Higher values indicate more consistent mechanics relative to your personal baseline.
        </p>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="formGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0d9488" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#0d9488" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} label={{ value: '% of run', position: 'insideBottomRight', offset: -10, fontSize: 11, fill: '#64748b' }} />
            <YAxis domain={[0, 110]} tick={{ fontSize: 11, fill: '#64748b' }} />
            <Tooltip content={<CustomTooltip />} />
            {onsetPct != null && (
              <ReferenceLine x={`${Math.round(onsetPct)}%`} stroke="#d97706" strokeDasharray="4 3"
                label={{ value: 'Form drift onset', position: 'top', fontSize: 11, fill: '#d97706' }} />
            )}
            <Area type="monotone" dataKey="form_quality" name="Form Quality" stroke="#0d9488" fill="url(#formGradient)" strokeWidth={2.5} dot={{ r: 4, fill: '#0d9488', strokeWidth: 0 }} activeDot={{ r: 6 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', padding: '0.5rem 0', marginBottom: '1rem' }}>
        {Object.entries(QUALITY_COLORS).map(([k, c]) => (
          <div key={k} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: c }} />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{k}</span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <div style={{ width: '24px', height: '2px', background: '#d97706', borderTop: '2px dashed #d97706' }} />
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Fatigue onset</span>
        </div>
      </div>

      {/* Detailed window breakdown */}
      {points.length > 0 && (
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Window Breakdown
          </h3>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {points.map(p => (
              <div key={p.window_index} title={`${p.form_quality}${p.notes.length > 0 ? ' — ' + p.notes.join(', ') : ''}`}
                style={{ width: '32px', height: '32px', borderRadius: '6px', background: QUALITY_COLORS[p.form_quality], opacity: p.is_baseline ? 1 : 0.85, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'default', fontSize: '0.65rem', color: '#ffffff', fontWeight: 700 }}>
                {p.is_baseline ? 'B' : ''}
              </div>
            ))}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.6rem' }}>B = Baseline window · Hover for notes</p>
        </div>
      )}
    </div>
  )
}
