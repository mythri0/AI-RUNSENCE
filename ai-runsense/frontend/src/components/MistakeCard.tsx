import { type Mistake } from '../api/client'
import { Play, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'
import { useState } from 'react'
import VoiceNarrator from './VoiceNarrator'

interface Props { mistake: Mistake; onReplay: () => void }

function fmtTime(s: number): string {
  const m = Math.floor(s / 60)
  const sec = (s % 60).toFixed(1)
  return `${m}:${sec.padStart(4, '0')}`
}

export default function MistakeCard({ mistake: m, onReplay }: Props) {
  const [expanded, setExpanded] = useState(false)

  const voiceText = `Detected issue: ${m.name}. Severity: ${m.severity}. Evidence: ${m.evidence}. ${m.suggested_correction ? `Correction: ${m.suggested_correction}` : ''}`

  return (
    <div className="glass-card" style={{ padding: '1.25rem', borderColor: m.severity === 'high' ? 'rgba(220,38,38,0.2)' : m.severity === 'medium' ? 'rgba(245,158,11,0.25)' : 'var(--border)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={16} color={m.severity === 'high' ? '#dc2626' : m.severity === 'medium' ? '#d97706' : '#059669'} />
          <h3 style={{ fontWeight: 700, fontSize: '0.97rem', color: 'var(--text-primary)', margin: 0 }}>{m.name}</h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <VoiceNarrator text={voiceText} compact />
          <span className={`badge-base badge-${m.severity}`}>{m.severity}</span>
        </div>
      </div>

      {/* Evidence */}
      <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: '0.85rem' }}>{m.evidence}</p>

      {/* Metrics chips */}
      {Object.entries(m.relevant_metrics).length > 0 && (
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.85rem' }}>
          {Object.entries(m.relevant_metrics).map(([k, v]) => v != null && (
            <span key={k} style={{ background: '#f1f5f9', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.2rem 0.55rem', fontSize: '0.73rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              {k}: {typeof v === 'number' ? v.toFixed(2) : String(v)}
            </span>
          ))}
        </div>
      )}

      {/* Confidence bar */}
      <div style={{ marginBottom: '0.9rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
          <span>Confidence</span>
          <span>{Math.round(m.confidence * 100)}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${m.confidence * 100}%`, background: m.confidence > 0.75 ? 'linear-gradient(90deg, #0d9488, #14b8a6)' : 'linear-gradient(90deg, #f59e0b, #fbbf24)' }} />
        </div>
      </div>

      {/* Expand */}
      <button onClick={() => setExpanded(e => !e)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', padding: 0, marginBottom: expanded ? '0.85rem' : 0, fontWeight: 500 }}>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {expanded ? 'Less detail' : 'More detail'}
      </button>

      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.85rem' }}>
          {m.possible_effect && (
            <div style={{ marginBottom: '0.75rem' }}>
              <p style={{ fontSize: '0.73rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Possible effect</p>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{m.possible_effect}</p>
            </div>
          )}
          {m.suggested_correction && (
            <div style={{ marginBottom: '0.75rem' }}>
              <p style={{ fontSize: '0.73rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-teal-dark)', marginBottom: '0.25rem' }}>Suggested correction</p>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{m.suggested_correction}</p>
            </div>
          )}
        </div>
      )}

      {/* Replay button */}
      {m.timestamp_s != null ? (
        <button className="btn-secondary" onClick={onReplay}
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', fontSize: '0.8rem', padding: '0.5rem', marginTop: '0.75rem', fontWeight: 600 }}>
          <Play size={13} fill="currentColor" /> Replay at {fmtTime(m.timestamp_s)}
        </button>
      ) : (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.75rem', fontStyle: 'italic' }}>
          Replay unavailable — general session pattern
        </p>
      )}
    </div>
  )
}
