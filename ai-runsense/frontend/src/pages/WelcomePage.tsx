import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, Zap, Target, TrendingUp, PlusCircle, User, LogOut, UserPlus, Sparkles, ArrowRight, Award, Calendar, Video, Clock } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { getRunnerRuns } from '../api/client'
import HeroSection from '../components/HeroSection'

interface RunItem {
  id: number
  status: string
  created_at: string
  distance_type?: string
  session_goal?: string
}

export default function WelcomePage() {
  const nav = useNavigate()
  const { user, logout } = useAuth()
  const runnerId = Number(localStorage.getItem('runner_id'))
  const [recentRuns, setRecentRuns] = useState<RunItem[]>([])
  const [filter, setFilter] = useState<'all' | 'done'>('all')

  useEffect(() => {
    if (user && runnerId) {
      getRunnerRuns(runnerId)
        .then(res => {
          if (Array.isArray(res.data)) {
            setRecentRuns(res.data)
          }
        })
        .catch(() => {})
    }
  }, [user, runnerId])

  const handleStart = () => {
    if (user) nav('/upload')
    else nav('/login')
  }

  const handleLogout = () => {
    logout()
    setRecentRuns([])
    nav('/')
  }

  const handleCreateNewUser = () => {
    logout()
    setRecentRuns([])
    nav('/register')
  }

  const features = [
    { icon: Activity, title: 'Real-time Pose AI', desc: 'Precise 2D trajectory tracking with joint angle kinematics on every video frame', color: '#0d9488' },
    { icon: Zap, title: 'Adaptive Baseline', desc: 'Learns your individual movement signature to identify subtle form drift and fatigue', color: '#f59e0b' },
    { icon: Target, title: 'Timestamped Replay', desc: 'Pinpoints exact seconds of biomechanical breakdown with looped visual feedback', color: '#0d9488' },
    { icon: TrendingUp, title: 'Evolution Engine', desc: 'Tracks multi-session progress, before/after symmetry, and personalized corrective drills', color: '#f59e0b' },
  ]

  const doneRuns = recentRuns.filter(r => r.status === 'done')
  const latestDoneRun = doneRuns[0]
  const displayedRuns = filter === 'done' ? doneRuns : recentRuns

  const isGuestOrNew = !user || recentRuns.length === 0

  return (
    <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden', background: isGuestOrNew ? '#090d16' : 'var(--bg-primary)' }}>
      {/* Top Navigation */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1.25rem 2.5rem',
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        zIndex: 20,
        backdropFilter: 'blur(12px)',
        background: isGuestOrNew ? 'rgba(9, 13, 22, 0.4)' : 'rgba(255, 255, 255, 0.85)',
        borderBottom: isGuestOrNew ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(226,232,240,0.8)',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => nav('/')}>
          <div style={{ width: '40px', height: '40px', background: 'linear-gradient(135deg, #0d9488, #0f766e)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(13,148,136,0.25)' }}>
            <Activity size={22} color="white" />
          </div>
          <div>
            <span style={{ fontSize: '1.2rem', fontWeight: 800, color: isGuestOrNew ? '#ffffff' : 'var(--text-primary)', letterSpacing: '-0.02em', display: 'block', lineHeight: 1.1 }}>AI RunSense</span>
            <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#2dd4bf', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Biomechanics Intelligence</span>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {user ? (
            <>
              <button onClick={() => nav('/evolution')} style={{ background: 'transparent', border: 'none', color: isGuestOrNew ? 'rgba(255,255,255,0.85)' : 'var(--text-secondary)', cursor: 'pointer', fontWeight: 600, fontSize: '0.88rem', padding: '0.5rem 0.75rem', borderRadius: '8px', transition: 'all 0.15s' }}>
                Evolution
              </button>
              <button onClick={() => nav('/profile')} style={{ background: 'transparent', border: 'none', color: isGuestOrNew ? 'rgba(255,255,255,0.85)' : 'var(--text-secondary)', cursor: 'pointer', fontWeight: 600, fontSize: '0.88rem', padding: '0.5rem 0.75rem', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <User size={16} /> {user.name || 'Profile'}
              </button>
              <button className="btn-primary" onClick={() => nav('/upload')} style={{ padding: '0.55rem 1.1rem', fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: '0.4rem', boxShadow: '0 4px 14px rgba(13,148,136,0.3)' }}>
                <PlusCircle size={16} /> Analyze Run
              </button>
              <button
                onClick={handleCreateNewUser}
                style={{
                  background: 'rgba(13,148,136,0.15)',
                  border: '1px solid rgba(45,212,191,0.3)',
                  color: '#2dd4bf',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem'
                }}
                title="Create a new runner profile"
              >
                <UserPlus size={15} /> New User
              </button>
              <button
                onClick={handleLogout}
                style={{
                  background: 'rgba(239,68,68,0.1)',
                  border: '1px solid rgba(239,68,68,0.3)',
                  color: '#f87171',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem'
                }}
                title="Log out of current account"
              >
                <LogOut size={15} /> Log Out
              </button>
            </>
          ) : (
            <>
              <button onClick={() => nav('/login')} style={{ background: 'transparent', border: 'none', color: '#ffffff', cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
                Sign In
              </button>
              <button className="btn-primary" onClick={() => nav('/register')} style={{ padding: '0.55rem 1.35rem', fontSize: '0.88rem' }}>
                Get Started Free
              </button>
            </>
          )}
        </nav>
      </header>

      {/* Main Content Area */}
      {user && recentRuns.length > 0 ? (
        <main style={{ maxWidth: '1180px', margin: '0 auto', padding: '7rem 1.5rem 4rem', position: 'relative', zIndex: 1 }}>
          <div>
            {/* Hero Welcome Banner for Logged-In User */}
            <div className="glass-card" style={{
              padding: '2rem 2.25rem',
              marginBottom: '2rem',
              background: 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,253,250,0.85))',
              border: '1px solid rgba(13,148,136,0.2)',
              boxShadow: '0 10px 30px rgba(13,148,136,0.06)',
              borderRadius: '20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1.5rem'
            }}>
              <div style={{ maxWidth: '640px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'var(--accent-teal-bg)', border: '1px solid var(--accent-teal-border)', padding: '0.25rem 0.75rem', borderRadius: '100px' }}>
                    <Sparkles size={14} color="var(--accent-teal-dark)" />
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-teal-dark)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Coach Ready</span>
                  </div>
                  {user?.email && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: '#f1f5f9', padding: '0.25rem 0.6rem', borderRadius: '6px' }}>
                      {user.email}
                    </span>
                  )}
                </div>
                <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem', lineHeight: 1.2 }}>
                  Welcome back, {user.name || 'Athlete'} 👋
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                  Track your cadence stability, pelvic symmetry, and timestamped running mechanics. Upload a new video, view trends, or switch accounts anytime.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <button className="btn-primary" onClick={() => nav('/upload')} style={{ padding: '0.75rem 1.5rem', fontSize: '0.92rem', display: 'flex', alignItems: 'center', gap: '0.5rem', borderRadius: '12px' }}>
                  <PlusCircle size={18} />
                  Analyze New Video
                </button>
                <button className="btn-secondary" onClick={() => nav('/evolution')} style={{ padding: '0.75rem 1.35rem', fontSize: '0.92rem', display: 'flex', alignItems: 'center', gap: '0.4rem', borderRadius: '12px' }}>
                  <TrendingUp size={17} color="var(--accent-teal-dark)" />
                  Evolution Trends
                </button>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2.5rem' }}>
              <div className="glass-card" style={{ padding: '1.4rem', borderRadius: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Analyzed Sessions</span>
                  <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-teal-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Activity size={16} color="var(--accent-teal-dark)" />
                  </div>
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-teal-dark)', lineHeight: 1 }}>{doneRuns.length}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>{recentRuns.length} total uploads processed</div>
              </div>

              {latestDoneRun && (
                <div className="glass-card" style={{ padding: '1.4rem', borderRadius: '16px', cursor: 'pointer', transition: 'transform 0.2s', border: '1px solid rgba(13,148,136,0.3)' }} onClick={() => nav(`/analysis/${latestDoneRun.id}`)}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Most Recent Session</span>
                    <span className="badge badge-green">DONE</span>
                  </div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                    Run #{latestDoneRun.id} · {latestDoneRun.distance_type || 'Training Run'}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-teal)', fontSize: '0.8rem', fontWeight: 600, marginTop: '0.5rem' }}>
                    Open Full Dashboard <ArrowRight size={14} />
                  </div>
                </div>
              )}

              <div className="glass-card" style={{ padding: '1.4rem', borderRadius: '16px', background: 'var(--accent-orange-bg)', border: '1px solid var(--accent-orange-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#b45309', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Biomechanical Health</span>
                  <Award size={18} color="#d97706" />
                </div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#92400e', marginBottom: '0.2rem' }}>
                  AI Coach Active
                </div>
                <div style={{ fontSize: '0.78rem', color: '#b45309' }}>Voice coaching & timestamp replays enabled</div>
              </div>
            </div>

            {/* Sessions Cards Grid */}
            <div style={{ marginBottom: '3rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                    Your Running Sessions
                  </h2>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0' }}>
                    Select any run to inspect video analysis, fatigue onset, and corrective feedback
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '0.4rem', background: '#f1f5f9', padding: '0.25rem', borderRadius: '10px' }}>
                  <button
                    onClick={() => setFilter('all')}
                    style={{
                      padding: '0.35rem 0.85rem',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      borderRadius: '8px',
                      border: 'none',
                      cursor: 'pointer',
                      background: filter === 'all' ? 'white' : 'transparent',
                      color: filter === 'all' ? 'var(--text-primary)' : 'var(--text-secondary)',
                      boxShadow: filter === 'all' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none',
                    }}
                  >
                    All ({recentRuns.length})
                  </button>
                  <button
                    onClick={() => setFilter('done')}
                    style={{
                      padding: '0.35rem 0.85rem',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      borderRadius: '8px',
                      border: 'none',
                      cursor: 'pointer',
                      background: filter === 'done' ? 'white' : 'transparent',
                      color: filter === 'done' ? 'var(--text-primary)' : 'var(--text-secondary)',
                      boxShadow: filter === 'done' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none',
                    }}
                  >
                    Completed ({doneRuns.length})
                  </button>
                </div>
              </div>

              {/* Session Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
                {displayedRuns.map(r => (
                  <div
                    key={r.id}
                    className="glass-card"
                    style={{
                      padding: '1.4rem',
                      borderRadius: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      position: 'relative',
                      border: r.status === 'done' ? '1px solid rgba(13,148,136,0.2)' : '1px solid var(--border)',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 4px 16px rgba(0,0,0,0.03)'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--text-primary)' }}>Run #{r.id}</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>•</span>
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Calendar size={13} /> {new Date(r.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <span className={`badge ${r.status === 'done' ? 'badge-green' : r.status === 'processing' ? 'badge-yellow' : 'badge-blue'}`}>
                          {r.status.toUpperCase()}
                        </span>
                      </div>

                      <div style={{ padding: '0.75rem 0', borderTop: '1px solid #f1f5f9', borderBottom: '1px solid #f1f5f9', margin: '0.5rem 0 1rem' }}>
                        <p style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                          {r.distance_type || 'Standard Form Assessment'}
                        </p>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.2rem', margin: 0 }}>
                          Goal: {r.session_goal || 'Biomechanical Optimization & Symmetry'}
                        </p>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                      {r.status === 'done' ? (
                        <>
                          <button
                            onClick={() => nav(`/analysis/${r.id}`)}
                            className="btn-primary"
                            style={{ flex: 1, padding: '0.55rem', fontSize: '0.84rem', justifyContent: 'center', borderRadius: '10px' }}
                          >
                            <Activity size={15} /> View Analysis
                          </button>
                          <button
                            onClick={() => nav(`/analysis/${r.id}`)}
                            className="btn-secondary"
                            style={{ padding: '0.55rem 0.85rem', fontSize: '0.84rem', borderRadius: '10px' }}
                            title="Open video replay directly"
                          >
                            <Video size={15} color="var(--accent-teal-dark)" />
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => nav(`/analysis/${r.id}`)}
                          className="btn-secondary"
                          style={{ width: '100%', padding: '0.55rem', fontSize: '0.84rem', justifyContent: 'center', borderRadius: '10px' }}
                        >
                          <Clock size={15} /> Resume Processing
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      ) : (
        /* Cinematic Video Hero Landing State */
        <div>
          <HeroSection
            onGetStarted={handleStart}
            onExploreEvolution={() => nav('/evolution')}
            userLoggedIn={!!user}
          />

          {/* Feature Grid Below Hero */}
          <div style={{ background: '#090d16', borderTop: '1px solid rgba(255,255,255,0.08)', padding: '4rem 2.5rem 6rem' }}>
            <div style={{ maxWidth: '1180px', margin: '0 auto' }}>
              <div style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto 3rem' }}>
                <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.6rem', fontFamily: "'Space Grotesk', sans-serif" }}>
                  Built for Serious Runners & Coaches
                </h2>
                <p style={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                  Professional biomechanics analysis powered by MediaPipe pose tracking, adaptive baselines, and timestamped flaw replay.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
                {features.map(({ icon: Icon, title, desc, color }) => (
                  <div
                    key={title}
                    style={{
                      padding: '1.75rem',
                      borderRadius: '18px',
                      background: 'rgba(15, 23, 42, 0.75)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(10px)',
                      textAlign: 'left',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div style={{ width: '48px', height: '48px', background: color === '#0d9488' ? 'rgba(13, 148, 136, 0.2)' : 'rgba(245, 158, 11, 0.2)', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem', border: `1px solid ${color === '#0d9488' ? 'rgba(45, 212, 191, 0.4)' : 'rgba(251, 191, 36, 0.4)'}` }}>
                      <Icon size={24} color={color === '#0d9488' ? '#2dd4bf' : '#fbbf24'} />
                    </div>
                    <h3 style={{ fontWeight: 800, fontSize: '1.05rem', marginBottom: '0.5rem', color: '#ffffff' }}>{title}</h3>
                    <p style={{ color: 'rgba(255, 255, 255, 0.65)', fontSize: '0.86rem', lineHeight: 1.6, margin: 0 }}>{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
