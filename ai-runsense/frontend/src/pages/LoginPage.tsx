import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import { Activity } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const nav = useNavigate()
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const res = await axios.post('/api/auth/login', formData)
      const token = res.data.access_token

      const userRes = await axios.get('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      login(token, userRes.data)
      nav('/upload')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', position: 'relative', overflow: 'hidden' }}>
      {/* Left decorative panel */}
      <div style={{ flex: 1, background: 'linear-gradient(160deg, #0d9488 0%, #0f766e 60%, #115e59 100%)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem', position: 'relative', minHeight: '100vh' }}>
        <div className="deco-circle float-anim" style={{ width: '200px', height: '200px', background: 'rgba(255,255,255,0.08)', top: '10%', left: '10%' }} />
        <div className="deco-circle float-anim-slow" style={{ width: '120px', height: '120px', background: 'rgba(245,158,11,0.2)', bottom: '20%', right: '15%' }} />
        <div className="deco-circle float-anim-fast" style={{ width: '80px', height: '80px', background: 'rgba(255,255,255,0.06)', top: '50%', left: '60%' }} />
        
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
          <div style={{ width: '80px', height: '80px', background: 'rgba(255,255,255,0.15)', borderRadius: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 2rem', backdropFilter: 'blur(10px)' }}>
            <Activity size={36} color="white" />
          </div>
          <h2 style={{ color: 'white', fontSize: '1.8rem', fontWeight: 800, fontFamily: "'Space Grotesk', sans-serif", marginBottom: '0.75rem' }}>AI RunSense</h2>
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.95rem', lineHeight: 1.6, maxWidth: '280px' }}>
            Transform your running with AI-powered biomechanics analysis.
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem', background: 'var(--bg-primary)' }}>
        <div style={{ maxWidth: '380px', width: '100%' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Welcome Back</h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem' }}>Log in to access your running data.</p>
          
          {error && <div style={{ background: 'rgba(220,38,38,0.06)', color: '#dc2626', padding: '0.75rem', borderRadius: '10px', marginBottom: '1.5rem', fontSize: '0.85rem', textAlign: 'center', border: '1px solid rgba(220,38,38,0.15)' }}>{error}</div>}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={labelStyle}>Email</label>
              <input className="input-field" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required />
            </div>
            <div>
              <label style={labelStyle}>Password</label>
              <input className="input-field" type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            <button className="btn-primary" type="submit" style={{ marginTop: '0.5rem', width: '100%' }}>Log In</button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Don't have an account? <button onClick={() => nav('/register')} style={{ background: 'none', border: 'none', color: 'var(--accent-teal)', cursor: 'pointer', fontWeight: 600 }}>Sign up</button>
          </p>
        </div>
      </div>
    </div>
  )
}

const labelStyle: React.CSSProperties = { display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }
