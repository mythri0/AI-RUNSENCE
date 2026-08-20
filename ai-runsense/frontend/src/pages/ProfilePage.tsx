import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, ArrowRight, ArrowLeft, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { updateProfile, type RunnerProfile } from '../api/client'

const EXPERIENCE_OPTIONS = ['Beginner', 'Intermediate', 'Advanced', 'Elite']
const GOAL_OPTIONS = ['Speed', 'Endurance', 'Technique', 'General Fitness', 'Race Preparation', 'Injury Prevention']
const GENDER_OPTIONS = ['Prefer not to say', 'Male', 'Female', 'Non-binary', 'Other']

export default function ProfilePage() {
  const nav = useNavigate()
  const { user, login, logout, token } = useAuth()
  
  const [form, setForm] = useState<RunnerProfile>({ 
    name: user?.name || '', 
    age: user?.age || undefined, 
    weight_kg: user?.weight_kg || undefined, 
    height_cm: user?.height_cm || undefined, 
    gender: user?.gender || '', 
    experience_level: user?.experience_level || '', 
    primary_goal: user?.primary_goal || '' 
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (k: keyof RunnerProfile, v: unknown) => setForm(f => ({ ...f, [k]: v }))

  const bmi = form.weight_kg && form.height_cm
    ? (form.weight_kg / Math.pow(form.height_cm / 100, 2)).toFixed(1)
    : null

  const handleSubmit = async () => {
    if (!form.age && !form.weight_kg && !form.height_cm) { setError('Please fill in at least some profile information.'); return }
    if (!user || !user.id || !token) { setError('Not logged in.'); return }
    setLoading(true); setError('')
    try {
      const res = await updateProfile(user.id, form)
      login(token, res.data) // Update auth context with new profile data
      localStorage.setItem('runner_id', String(user.id))
      localStorage.setItem('runner_data', JSON.stringify(res.data))
      nav('/context')
    } catch (e: unknown) {
      setError('Failed to save profile. Is the backend running?')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', background: 'var(--bg-primary)' }}>
      <div style={{ maxWidth: '520px', width: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <button onClick={() => nav('/')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <ArrowLeft size={16} /> Back to Dashboard
          </button>
          <button
            onClick={() => { logout(); nav('/') }}
            style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)', color: '#dc2626', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', padding: '0.35rem 0.75rem', borderRadius: '8px', fontWeight: 600 }}
          >
            <LogOut size={14} /> Log Out
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ width: '44px', height: '44px', background: 'var(--accent-teal-bg)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--accent-teal-border)' }}>
            <User size={20} color="var(--accent-teal)" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>Runner Profile</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Step 1 of 3 — Your information is never inferred from video</p>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.75rem', marginTop: '1.5rem' }}>
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <label style={labelStyle}>Name (optional)</label>
              <input className="input-field" placeholder="e.g. Alex" value={form.name || ''} onChange={e => set('name', e.target.value)} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={labelStyle}>Age (years)</label>
                <input className="input-field" type="number" min="5" max="100" placeholder="e.g. 32" value={form.age || ''} onChange={e => set('age', e.target.value ? Number(e.target.value) : undefined)} />
              </div>
              <div>
                <label style={labelStyle}>Gender (optional)</label>
                <select className="input-field" value={form.gender || ''} onChange={e => set('gender', e.target.value)}>
                  <option value="">— Select —</option>
                  {GENDER_OPTIONS.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={labelStyle}>Weight (kg)</label>
                <input className="input-field" type="number" min="30" max="300" placeholder="e.g. 70" value={form.weight_kg || ''} onChange={e => set('weight_kg', e.target.value ? Number(e.target.value) : undefined)} />
              </div>
              <div>
                <label style={labelStyle}>Height (cm)</label>
                <input className="input-field" type="number" min="100" max="250" placeholder="e.g. 175" value={form.height_cm || ''} onChange={e => set('height_cm', e.target.value ? Number(e.target.value) : undefined)} />
              </div>
            </div>

            {bmi && (
              <div style={{ background: 'rgba(5,150,105,0.06)', border: '1px solid rgba(5,150,105,0.15)', borderRadius: '10px', padding: '0.65rem 1rem', fontSize: '0.83rem', color: '#059669' }}>
                BMI: <strong>{bmi}</strong> — User-provided profile calculation (not used for analysis)
              </div>
            )}

            <div>
              <label style={labelStyle}>Experience Level</label>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {EXPERIENCE_OPTIONS.map(opt => (
                  <button key={opt} onClick={() => set('experience_level', opt)}
                    style={{ padding: '0.4rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer', border: '1px solid', borderColor: form.experience_level === opt ? 'var(--accent-teal)' : 'var(--border)', background: form.experience_level === opt ? 'var(--accent-teal-bg)' : 'transparent', color: form.experience_level === opt ? 'var(--accent-teal)' : 'var(--text-secondary)', transition: 'all 0.15s' }}>
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label style={labelStyle}>Primary Goal</label>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {GOAL_OPTIONS.map(opt => (
                  <button key={opt} onClick={() => set('primary_goal', opt)}
                    style={{ padding: '0.4rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer', border: '1px solid', borderColor: form.primary_goal === opt ? '#d97706' : 'var(--border)', background: form.primary_goal === opt ? 'var(--accent-orange-bg)' : 'transparent', color: form.primary_goal === opt ? '#d97706' : 'var(--text-secondary)', transition: 'all 0.15s' }}>
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            {error && <p style={{ color: '#dc2626', fontSize: '0.85rem' }}>{error}</p>}

            <button className="btn-primary" onClick={handleSubmit} disabled={loading} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
              {loading ? <><div className="spinner" style={{ width: 18, height: 18 }} /> Saving…</> : <>Continue <ArrowRight size={18} /></>}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const labelStyle: React.CSSProperties = { display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }
