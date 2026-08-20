import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, ArrowLeft } from 'lucide-react'

const DISTANCE_OPTIONS = [
  { value: 'sprint', label: 'Sprint', desc: '< 400m' },
  { value: 'middle', label: 'Middle Distance', desc: '800m – 5km' },
  { value: 'long', label: 'Long Distance', desc: '5km – 21km' },
  { value: 'marathon', label: 'Marathon', desc: '42km' },
  { value: 'ultra', label: 'Ultra Marathon', desc: '42km+' },
  { value: 'general', label: 'General Training', desc: 'Any distance' },
]

const ENV_OPTIONS = [
  { value: 'track', label: '🏟 Track', desc: 'Controlled surface' },
  { value: 'road', label: '🛣 Road', desc: 'Pavement/concrete' },
  { value: 'trail', label: '🌲 Trail', desc: 'Off-road terrain' },
  { value: 'treadmill', label: '⚙️ Treadmill', desc: 'Indoor machine' },
  { value: 'other', label: '📍 Other', desc: 'Other surface' },
]

const GOAL_OPTIONS = [
  { value: 'Improve Speed', label: '⚡ Improve Speed' },
  { value: 'Improve Endurance', label: '🫁 Improve Endurance' },
  { value: 'Improve Efficiency', label: '🎯 Improve Efficiency' },
  { value: 'Improve Technique', label: '🎨 Improve Technique' },
  { value: 'Injury Prevention', label: '🛡 Injury Prevention' },
]

export default function ContextPage() {
  const nav = useNavigate()
  const [distance, setDistance] = useState('')
  const [env, setEnv] = useState('')
  const [goal, setGoal] = useState('')

  const handleContinue = () => {
    if (!distance && !env && !goal) return
    localStorage.setItem('run_context', JSON.stringify({ distance_type: distance, environment: env, session_goal: goal }))
    nav('/upload')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', background: 'var(--bg-primary)' }}>
      <div style={{ maxWidth: '640px', width: '100%' }}>
        <button onClick={() => nav('/profile')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '2rem', fontSize: '0.85rem' }}>
          <ArrowLeft size={16} /> Back
        </button>

        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>Running Context</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Step 2 of 3 — Context-aware recommendations require this information</p>
        </div>

        {/* Distance */}
        <Section title="Distance / Type" icon="🏃">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.6rem' }}>
            {DISTANCE_OPTIONS.map(opt => (
              <OptionCard key={opt.value} label={opt.label} desc={opt.desc} selected={distance === opt.value} onClick={() => setDistance(opt.value)} />
            ))}
          </div>
        </Section>

        {/* Environment */}
        <Section title="Environment" icon="🌍">
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            {ENV_OPTIONS.map(opt => (
              <OptionCard key={opt.value} label={opt.label} desc={opt.desc} selected={env === opt.value} onClick={() => setEnv(opt.value)} compact />
            ))}
          </div>
        </Section>

        {/* Goal */}
        <Section title="Session Goal" icon="🎯">
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            {GOAL_OPTIONS.map(opt => (
              <button key={opt.value} onClick={() => setGoal(opt.value)}
                style={{ padding: '0.5rem 1.1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer', border: '1px solid', borderColor: goal === opt.value ? 'var(--accent-orange)' : 'var(--border)', background: goal === opt.value ? 'var(--accent-orange-bg)' : 'transparent', color: goal === opt.value ? '#d97706' : 'var(--text-secondary)', transition: 'all 0.15s' }}>
                {opt.label}
              </button>
            ))}
          </div>
        </Section>

        <button className="btn-primary" onClick={handleContinue} style={{ width: '100%', marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          Continue to Upload <ArrowRight size={18} />
        </button>
      </div>
    </div>
  )
}

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1rem' }}>
      <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '1rem' }}>
        {icon} {title}
      </h3>
      {children}
    </div>
  )
}

function OptionCard({ label, desc, selected, onClick, compact }: { label: string; desc: string; selected: boolean; onClick: () => void; compact?: boolean }) {
  return (
    <button onClick={onClick}
      style={{ padding: compact ? '0.5rem 0.9rem' : '0.75rem 1rem', borderRadius: '10px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer', border: '1px solid', borderColor: selected ? 'var(--accent-teal)' : 'var(--border)', background: selected ? 'var(--accent-teal-bg)' : '#f8fafc', color: selected ? 'var(--accent-teal-dark)' : 'var(--text-secondary)', textAlign: 'left', transition: 'all 0.15s' }}>
      <div style={{ fontWeight: 600 }}>{label}</div>
      {!compact && <div style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: '0.15rem' }}>{desc}</div>}
    </button>
  )
}
