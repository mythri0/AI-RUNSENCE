import { type Coach, type Priority } from '../api/client'
import { MessageSquare, Zap, CheckCircle, Target, TrendingUp } from 'lucide-react'
import VoiceNarrator from './VoiceNarrator'

interface Props { coach: Coach; priorities?: Priority[] }

export default function CoachPanel({ coach }: Props) {
  if (!coach) return <p style={{ color: 'var(--text-secondary)' }}>No coaching data available.</p>

  const fullCoachingScript = [
    coach.top_priority ? `Top Priority: ${coach.top_priority}` : '',
    Array.isArray(coach.focus_next) && coach.focus_next.length ? `What to focus on next: ${coach.focus_next.join('. ')}` : '',
    Array.isArray(coach.doing_well) && coach.doing_well.length ? `What you are doing well: ${coach.doing_well.join('. ')}` : '',
    Array.isArray(coach.what_changed) && coach.what_changed.length ? `Form changes detected: ${coach.what_changed.join('. ')}` : '',
  ].filter(Boolean).join('. ')

  const sections = [
    { key: 'doing_well', label: 'What You\'re Doing Well', icon: <CheckCircle size={16} color="#059669" />, color: '#059669', bg: 'rgba(5,150,105,0.06)', border: 'rgba(5,150,105,0.15)' },
    { key: 'what_changed', label: 'What Changed', icon: <TrendingUp size={16} color="#d97706" />, color: '#d97706', bg: 'var(--accent-orange-bg)', border: 'rgba(245,158,11,0.2)' },
    { key: 'why_it_matters', label: 'Why It May Matter', icon: <Zap size={16} color="#7c3aed" />, color: '#7c3aed', bg: 'rgba(124,58,237,0.06)', border: 'rgba(124,58,237,0.15)' },
    { key: 'focus_next', label: 'What to Focus On Next', icon: <Target size={16} color="#0d9488" />, color: '#0d9488', bg: 'var(--accent-teal-bg)', border: 'var(--accent-teal-border)' },
  ]

  return (
    <div>
      {/* AI source badge & Voice Narrator */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: coach.generated_by === 'gemini' ? 'var(--accent-teal-bg)' : '#f1f5f9', border: `1px solid ${coach.generated_by === 'gemini' ? 'var(--accent-teal-border)' : 'var(--border)'}`, borderRadius: '100px', padding: '0.35rem 0.85rem' }}>
          <MessageSquare size={13} color={coach.generated_by === 'gemini' ? 'var(--accent-teal)' : 'var(--text-secondary)'} />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: coach.generated_by === 'gemini' ? 'var(--accent-teal-dark)' : 'var(--text-secondary)' }}>
            {coach.generated_by === 'gemini' ? 'Gemini AI Coach' : 'Evidence-Based Coach (Deterministic)'}
          </span>
        </div>

        {fullCoachingScript && (
          <VoiceNarrator text={fullCoachingScript} title="Voice Coach Narration" />
        )}
      </div>

      {/* Top priority callout */}
      {coach.top_priority && (
        <div style={{ background: 'var(--accent-teal-bg)', border: '1px solid var(--accent-teal-border)', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
              <Target size={16} color="var(--accent-teal)" />
              <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--accent-teal-dark)' }}>Top Priority</span>
            </div>
            <p style={{ fontSize: '0.92rem', lineHeight: 1.6, color: 'var(--text-primary)', margin: 0 }}>{coach.top_priority}</p>
          </div>
          <VoiceNarrator text={coach.top_priority} compact />
        </div>
      )}

      {/* Coaching sections */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
        {sections.map(s => {
          const items: string[] = Array.isArray(coach[s.key as keyof Coach]) ? coach[s.key as keyof Coach] as string[] : []
          if (!items.length) return null
          return (
            <div key={s.key} style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                {s.icon}
                <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: s.color }}>{s.label}</span>
              </div>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {items.map((item, i) => (
                  <li key={i} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.87rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
                    <span style={{ color: s.color, flexShrink: 0, marginTop: '2px', fontWeight: 700 }}>·</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>

      {/* Context recommendation */}
      {coach.context_recommendation && (
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <p style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Context Recommendation</p>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{coach.context_recommendation}</p>
        </div>
      )}
    </div>
  )
}
