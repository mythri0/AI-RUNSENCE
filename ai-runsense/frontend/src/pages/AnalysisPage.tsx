import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Activity, Zap, Target, TrendingUp, Video, AlertTriangle, Home, ArrowLeft } from 'lucide-react'
import { getRunStatus, getFullAnalysis, videoUrl, type FullAnalysis, type Mistake, type Priority } from '../api/client'
import MetricsGrid from '../components/MetricsGrid'
import TimelineChart from '../components/TimelineChart'
import MistakeCard from '../components/MistakeCard'
import CoachPanel from '../components/CoachPanel'
import StyleRadar from '../components/StyleRadar'
import EfficiencyGauge from '../components/EfficiencyGauge'
import MistakeReplay from '../components/MistakeReplay'
import VoiceNarrator from '../components/VoiceNarrator'

const STAGES = [
  'Validating video…', 'Running pose estimation…', 'Building temporal trajectories…',
  'Detecting gait cycles…', 'Computing biomechanical metrics…', 'Computing personal baseline…',
  'Analyzing form degradation…', 'Computing loading index…', 'Classifying running style…',
  'Detecting form issues…', 'Ranking priorities…', 'Generating AI coaching…',
  'Writing annotated video…', 'Saving results…',
]

type TabId = 'overview' | 'metrics' | 'mistakes' | 'timeline' | 'coach' | 'video'

export default function AnalysisPage() {
  const { runId } = useParams<{ runId: string }>()
  const nav = useNavigate()
  const [data, setData] = useState<FullAnalysis | null>(null)
  const [pollingProgress, setPollingProgress] = useState(0)
  const [pollingStage, setPollingStage] = useState('Starting…')
  const [done, setDone] = useState(false)
  const [errored, setErrored] = useState(false)
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [selectedMistake, setSelectedMistake] = useState<Mistake | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!runId) return

    pollRef.current = setInterval(async () => {
      try {
        const res = await getRunStatus(Number(runId))
        const { status, processing_progress, processing_stage } = res.data
        setPollingProgress(processing_progress || 0)
        setPollingStage(processing_stage || '…')

        if (status === 'done') {
          clearInterval(pollRef.current!)
          const full = await getFullAnalysis(Number(runId))
          setData(full.data)
          setDone(true)
        } else if (status === 'error') {
          clearInterval(pollRef.current!)
          setErrored(true)
          setPollingStage(res.data.error_message || 'Unknown error')
        }
      } catch { /* network blip, keep polling */ }
    }, 1500)

    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [runId])

  if (errored) return <ErrorScreen msg={pollingStage} onBack={() => nav('/upload')} />
  if (!done) return <ProcessingScreen progress={pollingProgress} stage={pollingStage} />

  const d = data!
  const priorities = d.priorities || []
  const mistakes = d.mistakes || []

  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <Activity size={15} /> },
    { id: 'metrics', label: 'Metrics', icon: <Zap size={15} /> },
    { id: 'mistakes', label: `Issues (${mistakes.length})`, icon: <AlertTriangle size={15} /> },
    { id: 'timeline', label: 'Timeline', icon: <TrendingUp size={15} /> },
    { id: 'coach', label: 'AI Coach', icon: <Target size={15} /> },
    { id: 'video', label: 'Video', icon: <Video size={15} /> },
  ]

  return (
    <div style={{ minHeight: '100vh', maxWidth: '1200px', margin: '0 auto', padding: '0.75rem 1rem 2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        <button onClick={() => nav('/')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.82rem' }}>
          <Home size={14} /> Home
        </button>
        <span style={{ color: 'var(--border)' }}>·</span>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>Run Analysis <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 400 }}>#{runId}</span></h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', margin: 0 }}>
            {d.distance_type && <span style={{ marginRight: '0.75rem' }}>📏 {d.distance_type}</span>}
            {d.environment && <span style={{ marginRight: '0.75rem' }}>📍 {d.environment}</span>}
            {d.session_goal && <span>🎯 {d.session_goal}</span>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: '100px', padding: '0.25rem 0.7rem', alignItems: 'center' }}>
          <Activity size={13} color="#10b981" />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#10b981' }}>Analysis Complete</span>
        </div>
      </div>

      {/* Quick stats — compact inline row */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        <QuickStat label="Efficiency" value={`${d.efficiency?.overall?.toFixed(0) ?? '—'}/100`} color="#0d9488" compact />
        <QuickStat label="Cadence" value={d.metrics?.cadence?.value != null ? `${d.metrics.cadence.value.toFixed(0)} spm` : '—'} color="#0f766e" estimated={d.metrics?.cadence?.estimated} compact />
        <QuickStat label="Symmetry" value={d.metrics?.symmetry_index?.value != null ? `${d.metrics.symmetry_index.value.toFixed(0)}/100` : '—'} color="#059669" compact />
        <QuickStat label="Style" value={d.style?.primary_style ?? '—'} color="#d97706" compact />
        <QuickStat label="Issues" value={String(mistakes.length)} color={mistakes.some(m => m.severity === 'high') ? '#dc2626' : '#d97706'} compact />
        <QuickStat label="Fatigue" value={d.fatigue?.detected ? 'Detected' : 'OK'} color={d.fatigue?.detected ? '#d97706' : '#059669'} compact />
      </div>

      {/* Priority banner — compact single line */}
      {priorities[0] && (
        <div style={{ background: 'var(--accent-teal-bg)', border: '1px solid var(--accent-teal-border)', borderRadius: '10px', padding: '0.5rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flex: 1, minWidth: 0 }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent-teal-dark)', whiteSpace: 'nowrap' }}>🎯 #1</span>
            <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{priorities[0].name}</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>— {priorities[0].focus_tip}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
            <VoiceNarrator text={`Top Priority: ${priorities[0].name}. ${priorities[0].focus_tip}`} compact />
            <span className={`badge-base badge-${priorities[0].severity}`}>{priorities[0].severity}</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.15rem', borderBottom: '1px solid var(--border)', marginBottom: '0.85rem', flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.45rem 0.85rem', background: 'none', border: 'none', borderBottom: `2px solid ${activeTab === t.id ? 'var(--accent-teal)' : 'transparent'}`, color: activeTab === t.id ? 'var(--accent-teal-dark)' : 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.82rem', fontWeight: activeTab === t.id ? 700 : 500, transition: 'all 0.15s', marginBottom: '-1px' }}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div className="slide-up" key={activeTab}>
        {activeTab === 'overview' && <OverviewTab d={d} priorities={priorities} onGoMistakes={() => setActiveTab('mistakes')} onGoCoach={() => setActiveTab('coach')} onSelectMistake={m => { setSelectedMistake(m); setActiveTab('video') }} />}
        {activeTab === 'metrics' && <MetricsGrid metrics={d.metrics} />}
        {activeTab === 'mistakes' && <MistakesTab mistakes={mistakes} onReplay={m => { setSelectedMistake(m); setActiveTab('video') }} />}
        {activeTab === 'timeline' && <TimelineChart points={d.timeline} fatigue={d.fatigue} />}
        {activeTab === 'coach' && <CoachPanel coach={d.coach} priorities={priorities} />}
        {activeTab === 'video' && <VideoTab runId={Number(runId)} selectedMistake={selectedMistake} onClearMistake={() => setSelectedMistake(null)} gaitCycles={d.gait_cycles || []} />}
      </div>
    </div>
  )
}

// ── Sub-panels ─────────────────────────────────────────────────────────────────

function OverviewTab({ d, priorities, onGoCoach, onSelectMistake }: { d: FullAnalysis; priorities: Priority[]; onGoMistakes?: () => void; onGoCoach: () => void; onSelectMistake: (m: Mistake) => void }) {
  // Find which part of the video has the most critical issues / peak flaw window
  const mistakes = d.mistakes || []
  const timestampedMistakes = mistakes.filter(m => m.timestamp_s != null && !isNaN(m.timestamp_s))
  
  // Pick the highest severity or earliest critical flaw as the peak window center
  const highSev = timestampedMistakes.find(m => m.severity === 'high') || timestampedMistakes[0]
  const peakTs = highSev?.timestamp_s ?? d.fatigue?.onset_time_s ?? null
  const peakStart = peakTs != null ? Math.max(0, peakTs - 1.5) : null
  const peakEnd = peakTs != null ? peakTs + 2.0 : null

  return (
    <div>
      {/* HIGHEST ISSUE VIDEO WINDOW BANNER (First page dashboard spotlight) */}
      {peakTs != null && highSev && (
        <div className="glass-card" style={{
          padding: '0.65rem 1rem',
          marginBottom: '0.85rem',
          background: 'linear-gradient(135deg, rgba(254,242,242,0.95), rgba(255,247,237,0.9))',
          border: '1px solid rgba(239,68,68,0.25)',
          borderRadius: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.6rem',
          boxShadow: '0 2px 8px rgba(239,68,68,0.06)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flex: 1, minWidth: '220px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(239,68,68,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <AlertTriangle size={16} color="#dc2626" />
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.1rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#b91c1c', whiteSpace: 'nowrap' }}>Critical Zone</span>
                {peakStart != null && peakEnd != null && (
                  <span style={{ fontFamily: 'monospace', fontSize: '0.73rem', fontWeight: 700, color: '#dc2626', background: 'rgba(239,68,68,0.1)', padding: '0.1rem 0.35rem', borderRadius: '4px' }}>
                    {fmtTime(peakStart)} – {fmtTime(peakEnd)}
                  </span>
                )}
              </div>
              <p style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {highSev.name} {timestampedMistakes.length > 1 ? `+ ${timestampedMistakes.length - 1} other(s)` : ''}
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <VoiceNarrator text={`Critical form breakdown detected between ${peakStart != null ? fmtTime(peakStart) : '0:00'} and ${peakEnd != null ? fmtTime(peakEnd) : '0:00'}. Issue: ${highSev.name}. Evidence: ${highSev.evidence || ''}`} compact />
            <button
              onClick={() => onSelectMistake(highSev)}
              className="btn-primary"
              style={{
                padding: '0.6rem 1.25rem',
                fontSize: '0.84rem',
                background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
                boxShadow: '0 4px 12px rgba(220,38,38,0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                borderRadius: '10px'
              }}
            >
              <Video size={16} /> Replay Peak Flaw Zone
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '0.85rem' }}>
        {/* Style DNA */}
        <div className="glass-card" style={{ padding: '1rem' }}>
          <SectionTitle>Running Style DNA</SectionTitle>
          <StyleRadar style={d.style} />
          {d.style?.evidence?.length > 0 && (
            <div style={{ marginTop: '0.6rem' }}>
              {d.style.evidence.slice(0, 2).map((e, i) => <p key={i} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>· {e}</p>)}
            </div>
          )}
        </div>

        {/* Efficiency gauge */}
        <div className="glass-card" style={{ padding: '1rem' }}>
          <SectionTitle>Efficiency Score</SectionTitle>
          <EfficiencyGauge score={d.efficiency?.overall} components={d.efficiency?.components} />
        </div>

        {/* Top priorities */}
        <div className="glass-card" style={{ padding: '1.5rem', gridColumn: priorities.length > 0 ? 'auto' : undefined }}>
          <SectionTitle>Top Priorities</SectionTitle>
          {priorities.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>No significant form issues detected.</p>
          ) : (
            <>
              {priorities.map(p => (
                <div key={p.id} style={{ marginBottom: '0.75rem', padding: '0.9rem', background: '#f8fafc', border: '1px solid var(--border)', borderRadius: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{p.rank}. {p.name}</span>
                    <span className={`badge-base badge-${p.severity}`}>{p.severity}</span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{p.focus_tip}</p>
                  {p.timestamp_s != null && (
                    <button onClick={() => onSelectMistake({ ...p, severity: (p.severity as 'high' | 'medium' | 'low') || 'medium' })}
                      style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--accent-teal)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontWeight: 600 }}>
                      ▶ Replay at {fmtTime(p.timestamp_s)}
                    </button>
                  )}
                </div>
              ))}
              <button className="btn-secondary" onClick={onGoCoach} style={{ width: '100%', marginTop: '0.5rem', fontSize: '0.85rem' }}>
                View AI Coaching →
              </button>
            </>
          )}
        </div>

        {/* Fatigue */}
        {d.fatigue && (
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <SectionTitle>Form Degradation</SectionTitle>
            {d.fatigue.detected ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
                  <AlertTriangle size={18} color="#d97706" />
                  <span style={{ fontWeight: 600, color: '#d97706' }}>Pattern Detected</span>
                  {d.fatigue.onset_time_s != null && <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>~{fmtTime(d.fatigue.onset_time_s)}</span>}
                </div>
                {d.fatigue.drifting_metrics?.slice(0, 3).map(m => (
                  <div key={m.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border)', fontSize: '0.83rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{m.name}</span>
                    <span style={{ color: m.direction === 'decreasing' ? '#dc2626' : '#d97706', fontWeight: 600 }}>{m.direction}</span>
                  </div>
                ))}
                <p style={{ marginTop: '0.75rem', fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{d.fatigue.summary}</p>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-green)' }}>
                <Activity size={18} /> <span style={{ fontWeight: 600 }}>No significant form degradation detected</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function MistakesTab({ mistakes, onReplay }: { mistakes: Mistake[]; onReplay: (m: Mistake) => void }) {
  if (mistakes.length === 0) return (
    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
      <Activity size={40} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
      <p style={{ fontSize: '1rem', fontWeight: 600 }}>No significant form issues detected</p>
      <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>Your running mechanics look solid in this session.</p>
    </div>
  )

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1rem' }}>
      {mistakes.map(m => <MistakeCard key={m.id} mistake={m} onReplay={() => onReplay(m)} />)}
    </div>
  )
}

function VideoTab({ runId, selectedMistake, onClearMistake, gaitCycles }: { runId: number; selectedMistake: Mistake | null; onClearMistake: () => void; gaitCycles: FullAnalysis['gait_cycles'] }) {
  const [mode, setMode] = useState<'original' | 'pose' | 'analysis'>('original')
  const [hasError, setHasError] = useState(false)
  const [metaReady, setMetaReady] = useState(false)
  const [pendingSeek, setPendingSeek] = useState<number | null>(null)
  const mainVidRef = useRef<HTMLVideoElement>(null)
  const url = videoUrl(runId, mode)

  // Safe seek: if metadata is ready, seek immediately; otherwise queue the seek
  const seekToTime = (time_s: number) => {
    const vid = mainVidRef.current
    if (!vid) return
    if (metaReady && vid.readyState >= 1 && !isNaN(vid.duration)) {
      const clamped = Math.min(Math.max(0, time_s), vid.duration)
      vid.currentTime = clamped
      vid.play().catch(() => {})
    } else {
      setPendingSeek(time_s)
    }
  }

  const onLoadedMetadata = () => {
    setMetaReady(true)
    setHasError(false)
    if (pendingSeek !== null && mainVidRef.current) {
      const dur = mainVidRef.current.duration
      const clamped = Math.min(Math.max(0, pendingSeek), (!isNaN(dur) ? dur : pendingSeek))
      mainVidRef.current.currentTime = clamped
      mainVidRef.current.play().catch(() => {})
      setPendingSeek(null)
    }
  }

  const onError = () => {
    setHasError(true)
    setMetaReady(false)
  }

  const onModeChange = (m: 'original' | 'pose' | 'analysis') => {
    setHasError(false)
    setMetaReady(false)
    setPendingSeek(null)
    setMode(m)
  }

  return (
    <div>
      {selectedMistake ? (
        <MistakeReplay mistake={selectedMistake} runId={runId} onClose={onClearMistake} />
      ) : (
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          {/* Mode selector */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            {(['original', 'pose', 'analysis'] as const).map(m => (
              <button
                key={m}
                className={`video-tab${mode === m ? ' active' : ''}`}
                onClick={() => onModeChange(m)}
              >
                {m === 'original' ? '📹 Original' : m === 'pose' ? '🦴 Pose Overlay' : '🔍 Analysis'}
              </button>
            ))}
          </div>

          <div style={{ borderRadius: '10px', overflow: 'hidden', background: '#000', minHeight: '300px' }}>
            {hasError ? (
              <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: '#fff' }}>
                <AlertTriangle size={36} color="#f59e0b" style={{ margin: '0 auto 0.75rem' }} />
                <p style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.4rem' }}>
                  Video could not be loaded
                </p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
                  Try switching to Original mode, or click Retry.
                </p>
                <button className="btn-primary"
                  onClick={() => { setHasError(false); setMetaReady(false); if (mainVidRef.current) mainVidRef.current.load() }}
                  style={{ fontSize: '0.82rem' }}>
                  Retry Video
                </button>
              </div>
            ) : (
              <video
                ref={mainVidRef}
                key={url}
                src={url}
                controls
                preload="auto"
                playsInline
                onLoadedMetadata={onLoadedMetadata}
                onCanPlay={() => { const rs = mainVidRef.current?.readyState ?? 0; if (!metaReady && rs >= 1) onLoadedMetadata() }}
                onError={onError}
                onStalled={() => {}}
                style={{ width: '100%', maxHeight: '520px', display: 'block' }}
              />
            )}
          </div>

          <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            💡 Click any gait cycle or issue replay below to jump directly to that moment
          </p>

          {/* Gait cycle chips */}
          {gaitCycles.length > 0 && (
            <div style={{ marginTop: '1.25rem' }}>
              <p style={{ fontSize: '0.82rem', fontWeight: 700, marginBottom: '0.6rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Detected Gait Cycles ({gaitCycles.length}) · Click to Seek
              </p>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {gaitCycles.map(c => (
                  <button
                    key={c.index}
                    onClick={() => seekToTime(c.start_time_s)}
                    style={{
                      background: 'var(--accent-teal-bg)',
                      border: '1px solid var(--accent-teal-border)',
                      borderRadius: '6px',
                      padding: '0.25rem 0.65rem',
                      fontSize: '0.78rem',
                      color: 'var(--accent-teal-dark)',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s',
                    }}
                    title={`Seek to cycle #${c.index} at ${c.start_time_s.toFixed(2)}s (${c.duration_s.toFixed(2)}s long)`}
                  >
                    ▶ #{c.index} @ {fmtTime(c.start_time_s)}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Utility components ─────────────────────────────────────────────────────────

function QuickStat({ label, value, color, estimated, compact }: { label: string; value: string; color: string; estimated?: boolean; compact?: boolean }) {
  if (compact) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '100px', padding: '0.3rem 0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)', flexShrink: 0 }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>{label}</span>
        <span style={{ fontSize: '0.82rem', fontWeight: 800, color }}>{value}{estimated ? ' ~' : ''}</span>
      </div>
    )
  }
  return (
    <div className="metric-card">
      <p style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>{label}</p>
      <p style={{ fontSize: '1.35rem', fontWeight: 800, color, lineHeight: 1 }}>{value}</p>
      {estimated && <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>estimated</p>}
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)', marginBottom: '1rem' }}>{children}</h3>
}

function ProcessingScreen({ progress, stage }: { progress: number; stage: string }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', textAlign: 'center' }}>
      <div style={{ maxWidth: '500px', width: '100%' }}>
        <div className="pulse-glow" style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(59,130,246,0.15)', border: '2px solid rgba(59,130,246,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 2rem' }}>
          <Activity size={36} color="#60a5fa" />
        </div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>Analyzing Your Run</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem' }}>Running 15-stage AI pipeline…</p>
        <div className="progress-bar" style={{ height: '6px', marginBottom: '0.75rem' }}>
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          <span>{stage}</span>
          <span style={{ fontWeight: 600, color: '#60a5fa' }}>{progress.toFixed(0)}%</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '0.35rem', marginTop: '1.5rem' }}>
          {STAGES.map((s, i) => (
            <div key={s} title={s} style={{ height: '4px', borderRadius: '2px', background: progress >= (i / STAGES.length) * 100 ? '#3b82f6' : 'rgba(255,255,255,0.08)', transition: 'background 0.5s' }} />
          ))}
        </div>
      </div>
    </div>
  )
}

function ErrorScreen({ msg, onBack }: { msg: string; onBack: () => void }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', textAlign: 'center' }}>
      <AlertTriangle size={48} color="#ef4444" style={{ marginBottom: '1rem' }} />
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>Analysis Error</h1>
      <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', fontSize: '0.9rem', marginBottom: '1.5rem' }}>{msg}</p>
      <button className="btn-primary" onClick={onBack}><ArrowLeft size={16} /> Try Again</button>
    </div>
  )
}

function fmtTime(s: number): string {
  const m = Math.floor(s / 60)
  const sec = (s % 60).toFixed(1)
  return `${m}:${sec.padStart(4, '0')}`
}
