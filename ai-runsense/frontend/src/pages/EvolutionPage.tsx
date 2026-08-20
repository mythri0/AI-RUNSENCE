import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Home, Activity, ArrowUpRight, ArrowDownRight, Minus, TrendingUp, Sparkles } from 'lucide-react'
import { getEvolution } from '../api/client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface EvSession {
  session_id: number
  date: string
  efficiency_score?: number
  cadence_mean?: number
  symmetry_mean?: number
  posture_score?: number
  vertical_oscillation?: number
  trunk_lean?: number
  pelvic_stability?: number
  fatigue_detected: boolean
  issues_count?: number
  primary_style?: string
  distance_type?: string
}

export default function EvolutionPage() {
  const nav = useNavigate()
  const runnerId = Number(localStorage.getItem('runner_id'))
  const [data, setData] = useState<{ sessions: EvSession[] } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!runnerId) { setLoading(false); return }
    getEvolution(runnerId)
      .then(r => setData(r.data as { sessions: EvSession[] }))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [runnerId])

  if (!runnerId) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem', background: 'var(--bg-primary)' }}>
      <p style={{ color: 'var(--text-secondary)' }}>No runner profile found.</p>
      <button className="btn-primary" onClick={() => nav('/profile')}>Create Profile</button>
    </div>
  )

  const sessions = data?.sessions || []
  const hasHistory = sessions.length >= 2

  const firstRun = sessions[0]
  const latestRun = sessions[sessions.length - 1]

  const chartData = sessions.map((s, i) => ({
    session: `Run ${i + 1}`,
    efficiency: s.efficiency_score ? Number(s.efficiency_score.toFixed(1)) : null,
    cadence: s.cadence_mean ? Number(s.cadence_mean.toFixed(0)) : null,
    symmetry: s.symmetry_mean ? Number(s.symmetry_mean.toFixed(0)) : null,
    posture: s.posture_score ? Number(s.posture_score.toFixed(0)) : null,
    date: new Date(s.date).toLocaleDateString(),
  }))

  return (
    <div style={{ minHeight: '100vh', maxWidth: '1100px', margin: '0 auto', padding: '1.5rem 1rem 3rem', background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button onClick={() => nav('/')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <Home size={15} /> Home
          </button>
          <span style={{ color: 'var(--border)' }}>·</span>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>Biomechanics Evolution</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              {sessions.length} recorded session{sessions.length !== 1 ? 's' : ''} in historical baseline
            </p>
          </div>
        </div>

        <button className="btn-primary" onClick={() => nav('/upload')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          + Analyze New Run
        </button>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)', padding: '2rem' }}>
          <div className="spinner" /> Loading evolution data…
        </div>
      ) : sessions.length < 2 ? (
        <div className="glass-card" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
          <Activity size={48} color="var(--accent-teal)" style={{ margin: '0 auto 1.25rem', opacity: 0.7 }} />
          <h2 style={{ fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '1.3rem' }}>
            {sessions.length === 1 ? 'First Run Recorded' : 'No Recorded Runs Yet'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.75rem', maxWidth: '480px', margin: '0 auto 1.75rem' }}>
            {sessions.length === 1
              ? 'You have 1 recorded run. Complete a second run analysis to unlock before/after comparisons and progress trends.'
              : 'Upload and analyze running videos to begin tracking your biomechanical progression over time.'}
          </p>
          <button className="btn-primary" onClick={() => nav('/upload')}>Analyze a Run</button>
        </div>
      ) : (
        <>
          {/* Before vs After comparison card */}
          {hasHistory && (
            <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.75rem', background: 'linear-gradient(135deg, #ffffff 0%, rgba(20,184,166,0.03) 100%)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                <Sparkles size={18} color="var(--accent-teal)" />
                <h3 style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
                  Progress Comparison (Run 1 vs Latest Run {sessions.length})
                </h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <CompareItem
                  label="Efficiency Score"
                  before={firstRun.efficiency_score}
                  after={latestRun.efficiency_score}
                  unit="/100"
                  higherIsBetter={true}
                />
                <CompareItem
                  label="Cadence Turnover"
                  before={firstRun.cadence_mean}
                  after={latestRun.cadence_mean}
                  unit=" SPM"
                  higherIsBetter={true}
                />
                <CompareItem
                  label="Bilateral Symmetry"
                  before={firstRun.symmetry_mean}
                  after={latestRun.symmetry_mean}
                  unit="/100"
                  higherIsBetter={true}
                />
                <CompareItem
                  label="Detected Issues"
                  before={firstRun.issues_count ?? 0}
                  after={latestRun.issues_count ?? 0}
                  unit=" issues"
                  higherIsBetter={false}
                />
              </div>
            </div>
          )}

          {/* Metric Trends Chart */}
          <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <TrendingUp size={18} color="var(--accent-teal)" />
              <h3 style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
                Multi-Session Trend Trajectory
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 5, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="session" tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid var(--border)', borderRadius: '10px', fontSize: '0.82rem', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
                <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '0.82rem' }} />
                <Line type="monotone" dataKey="efficiency" name="Efficiency Score" stroke="#0d9488" strokeWidth={2.5} dot={{ fill: '#0d9488', r: 4 }} />
                <Line type="monotone" dataKey="symmetry" name="Symmetry Index" stroke="#059669" strokeWidth={2} dot={{ fill: '#059669', r: 4 }} />
                <Line type="monotone" dataKey="posture" name="Posture Score" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Session History Table */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
              Historical Session Log
            </h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.87rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)', background: '#f8fafc' }}>
                    {['Run #', 'Date', 'Distance / Focus', 'Efficiency', 'Cadence', 'Symmetry', 'Fatigue', 'Issues', ''].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '0.65rem 0.75rem', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s, idx) => (
                    <tr key={s.session_id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.15s' }}>
                      <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>#{idx + 1}</td>
                      <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-secondary)' }}>{new Date(s.date).toLocaleDateString()}</td>
                      <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-primary)', fontWeight: 500 }}>{s.distance_type || 'General'}</td>
                      <td style={{ padding: '0.65rem 0.75rem', fontWeight: 700, color: 'var(--accent-teal)' }}>{s.efficiency_score?.toFixed(1) ?? '—'}</td>
                      <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-primary)' }}>{s.cadence_mean?.toFixed(0) ?? '—'} SPM</td>
                      <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-primary)' }}>{s.symmetry_mean?.toFixed(0) ?? '—'}/100</td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        {s.fatigue_detected ? <span style={{ color: '#d97706', fontWeight: 600 }}>Detected</span> : <span style={{ color: '#059669', fontWeight: 600 }}>Stable</span>}
                      </td>
                      <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-secondary)' }}>{s.issues_count ?? 0}</td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <button onClick={() => nav(`/analysis/${s.session_id}`)} style={{ background: 'var(--accent-teal-bg)', border: '1px solid var(--accent-teal-border)', borderRadius: '6px', padding: '0.25rem 0.65rem', cursor: 'pointer', color: 'var(--accent-teal-dark)', fontSize: '0.78rem', fontWeight: 600 }}>View Run</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function CompareItem({
  label,
  before,
  after,
  unit,
  higherIsBetter,
}: {
  label: string
  before?: number | null
  after?: number | null
  unit: string
  higherIsBetter: boolean
}) {
  if (before == null || after == null) return null

  const diff = after - before
  const isPositive = higherIsBetter ? diff > 0 : diff < 0
  const isNeutral = Math.abs(diff) < 0.1

  return (
    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
      <p style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
        {label}
      </p>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.25rem' }}>
        <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          {after.toFixed(1)}{unit}
        </span>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          (was {before.toFixed(1)}{unit})
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.78rem', fontWeight: 600, color: isNeutral ? 'var(--text-secondary)' : isPositive ? '#059669' : '#dc2626' }}>
        {isNeutral ? <Minus size={14} /> : isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
        <span>{diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1)}{unit} delta</span>
      </div>
    </div>
  )
}
