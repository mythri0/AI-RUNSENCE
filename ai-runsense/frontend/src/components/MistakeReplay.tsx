import { useCallback, useEffect, useRef, useState } from 'react'
import { type Mistake, videoUrl } from '../api/client'
import { ArrowLeft, Play, Pause, AlertTriangle, Activity, RefreshCw } from 'lucide-react'

import VoiceNarrator from './VoiceNarrator'

interface Props {
  mistake: Mistake
  runId: number
  onClose: () => void
}

function fmtTime(s?: number | null): string {
  if (s == null || isNaN(s)) return '00:00.0'
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${String(m).padStart(2, '0')}:${sec.toFixed(1).padStart(4, '0')}`
}

export default function MistakeReplay({ mistake: m, runId, onClose }: Props) {
  const vidRef = useRef<HTMLVideoElement>(null)
  const [mode, setMode] = useState<'pose' | 'original' | 'analysis'>('pose')
  const [playing, setPlaying] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [metaReady, setMetaReady] = useState(false)
  const loopRef = useRef<boolean>(true)
  const endRef = useRef<number>(0)
  const startRef = useRef<number>(0)

  const currentUrl = videoUrl(runId, mode)

  // Compute replay window — clamp start to 0, end will be clamped to duration after metadata
  const targetTs = (m.timestamp_s != null && !isNaN(m.timestamp_s)) ? m.timestamp_s : 0
  const startTime = Math.max(0, targetTs - 1.5)
  const endTime = targetTs + 2.0

  startRef.current = startTime

  const doSeekAndPlay = useCallback(() => {
    const vid = vidRef.current
    if (!vid) return
    // Clamp end to actual duration
    const dur = vid.duration
    const safeEnd = (!isNaN(dur) && isFinite(dur)) ? Math.min(endTime, dur) : endTime
    const safeStart = Math.min(startTime, safeEnd - 0.1)
    endRef.current = safeEnd

    vid.currentTime = Math.max(0, safeStart)
    const p = vid.play()
    if (p) {
      p.then(() => setPlaying(true)).catch(() => {
        // Autoplay blocked — user must click play manually
        setPlaying(false)
      })
    }
  }, [startTime, endTime])

  // When metadata loads, we know duration — seek and play
  const onLoadedMetadata = useCallback(() => {
    setMetaReady(true)
    setHasError(false)
    doSeekAndPlay()
  }, [doSeekAndPlay])

  // Fallback: canplay fires after enough data to start
  const onCanPlay = useCallback(() => {
    if (!metaReady) {
      setMetaReady(true)
      doSeekAndPlay()
    }
  }, [metaReady, doSeekAndPlay])

  // Time-update loop: restart at startTime when end of window is reached
  const onTimeUpdate = useCallback(() => {
    const vid = vidRef.current
    if (!vid || !loopRef.current) return
    if (vid.currentTime >= endRef.current) {
      vid.currentTime = startRef.current
    }
  }, [])

  const onError = useCallback(() => {
    setHasError(true)
    setPlaying(false)
  }, [])

  const onPause = useCallback(() => setPlaying(false), [])
  const onPlay = useCallback(() => setPlaying(true), [])

  // Reset when mode or mistake changes
  useEffect(() => {
    setMetaReady(false)
    setHasError(false)
    setPlaying(false)
    loopRef.current = true
    // If video element already has enough metadata (cached), seek immediately
    const vid = vidRef.current
    if (vid && vid.readyState >= 1) {
      doSeekAndPlay()
    }
  }, [m.id, mode]) // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = () => {
    const vid = vidRef.current
    if (!vid) return
    if (playing) {
      loopRef.current = false
      vid.pause()
    } else {
      loopRef.current = true
      vid.play().then(() => setPlaying(true)).catch(() => {})
    }
  }

  const retry = () => {
    setHasError(false)
    setMetaReady(false)
    setPlaying(false)
    loopRef.current = true
    if (vidRef.current) {
      vidRef.current.load()
    }
  }

  return (
    <div className="glass-card" style={{ padding: '1.25rem', borderColor: m.severity === 'high' ? 'rgba(239,68,68,0.3)' : 'var(--border)' }}>

      {/* Top bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', padding: 0, fontWeight: 600 }}
        >
          <ArrowLeft size={16} /> Back to full video
        </button>

        <div style={{ display: 'flex', gap: '0.35rem' }}>
          {(['pose', 'original', 'analysis'] as const).map(mKey => (
            <button
              key={mKey}
              className={`video-tab${mode === mKey ? ' active' : ''}`}
              onClick={() => setMode(mKey)}
              style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
            >
              {mKey === 'original' ? '📹 Original' : mKey === 'pose' ? '🦴 Pose' : '🔍 Analysis'}
            </button>
          ))}
        </div>
      </div>

      {/* Evidence banner */}
      <div style={{
        background: 'rgba(245,158,11,0.08)',
        border: '1px solid rgba(245,158,11,0.25)',
        borderRadius: '8px',
        padding: '0.65rem 1rem',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <AlertTriangle size={18} color={m.severity === 'high' ? '#ef4444' : '#f59e0b'} />
          <div>
            <span style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#b45309' }}>
              REPLAYING EVIDENCE
            </span>
            <p style={{ fontSize: '0.98rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              {m.name}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <VoiceNarrator text={`Replaying flaw ${m.name}. Time window: ${fmtTime(startTime)} to ${fmtTime(endTime)}. Evidence: ${m.evidence}. Suggested correction: ${m.suggested_correction || ''}`} compact />
          <span style={{ fontFamily: 'monospace', fontSize: '0.82rem', fontWeight: 700, color: '#b45309', background: 'rgba(245,158,11,0.15)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
            {fmtTime(startTime)} – {fmtTime(endTime)}
          </span>
          <span className={`badge ${m.severity === 'high' ? 'badge-red' : m.severity === 'medium' ? 'badge-yellow' : 'badge-blue'}`}>
            {m.severity.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Video area */}
      <div style={{ position: 'relative', borderRadius: '10px', overflow: 'hidden', background: '#000', marginBottom: '1rem', minHeight: '260px' }}>
        {hasError ? (
          <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: '#fff' }}>
            <AlertTriangle size={36} color="#f59e0b" style={{ margin: '0 auto 0.75rem' }} />
            <p style={{ fontWeight: 600, marginBottom: '0.4rem' }}>Video stream could not be loaded</p>
            <p style={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
              Switch to Original mode or try again.
            </p>
            <button className="btn-primary" onClick={retry}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem' }}>
              <RefreshCw size={14} /> Retry
            </button>
          </div>
        ) : (
          <>
            <video
              ref={vidRef}
              key={`${runId}-${mode}`}
              src={currentUrl}
              preload="auto"
              playsInline
              controls
              onLoadedMetadata={onLoadedMetadata}
              onCanPlay={onCanPlay}
              onTimeUpdate={onTimeUpdate}
              onError={onError}
              onPause={onPause}
              onPlay={onPlay}
              style={{ width: '100%', maxHeight: '480px', display: 'block' }}
            />
            {/* Manual play/pause overlay button (for autoplay blocked) */}
            {!playing && metaReady && (
              <button
                onClick={toggle}
                style={{
                  position: 'absolute', bottom: '3.5rem', left: '50%', transform: 'translateX(-50%)',
                  width: '50px', height: '50px', borderRadius: '50%',
                  background: 'rgba(0,0,0,0.75)', border: '1px solid rgba(255,255,255,0.4)',
                  color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer', backdropFilter: 'blur(6px)',
                }}
                title="Play Replay"
              >
                <Play size={20} fill="currentColor" style={{ marginLeft: '3px' }} />
              </button>
            )}
            {playing && (
              <button
                onClick={toggle}
                style={{
                  position: 'absolute', bottom: '3.5rem', left: '50%', transform: 'translateX(-50%)',
                  width: '50px', height: '50px', borderRadius: '50%',
                  background: 'rgba(0,0,0,0.65)', border: '1px solid rgba(255,255,255,0.3)',
                  color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer', backdropFilter: 'blur(6px)',
                }}
                title="Pause Replay"
              >
                <Pause size={18} fill="currentColor" />
              </button>
            )}
          </>
        )}
      </div>

      {/* Active joints */}
      {m.highlight_joints && m.highlight_joints.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.85rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Activity size={13} /> Joint Focus:
          </span>
          {m.highlight_joints.map(j => (
            <span key={j} style={{ background: 'var(--accent-teal-bg)', border: '1px solid var(--accent-teal-border)', borderRadius: '4px', padding: '0.15rem 0.5rem', fontSize: '0.72rem', color: 'var(--accent-teal-dark)', fontWeight: 600 }}>
              {j.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {/* Evidence */}
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '0.85rem' }}>
        {m.evidence}
      </p>

      {m.possible_effect && (
        <div style={{ marginBottom: '0.85rem', padding: '0.75rem 1rem', borderRadius: '8px', background: 'rgba(239,68,68,0.04)', border: '1px solid rgba(239,68,68,0.15)' }}>
          <p style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#dc2626', marginBottom: '0.25rem' }}>Biomechanical Impact</p>
          <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{m.possible_effect}</p>
        </div>
      )}

      <div style={{ background: 'var(--accent-teal-bg)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--accent-teal-border)' }}>
        <p style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-teal-dark)', marginBottom: '0.3rem' }}>Suggested Action & Drill</p>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{m.suggested_correction}</p>
      </div>
    </div>
  )
}
