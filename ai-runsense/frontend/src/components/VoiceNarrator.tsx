import { useState, useEffect, useRef } from 'react'
import { Volume2, VolumeX, Pause, Play } from 'lucide-react'

interface VoiceNarratorProps {
  text: string
  title?: string
  autoPlay?: boolean
  compact?: boolean
}

function CoachAvatar({ speaking, size = 42 }: { speaking: boolean, size?: number }) {
  return (
    <div style={{ 
      position: 'relative', 
      width: `${size}px`, 
      height: `${size}px`, 
      flexShrink: 0,
      marginRight: '4px'
    }}>
      <svg viewBox="0 0 100 100" width="100%" height="100%">
        <style>{`
          .arm-point {
            transform-origin: 30px 60px;
            animation: ${speaking ? 'pointArm 1.5s infinite alternate ease-in-out' : 'none'};
          }
          .mouth-talk {
            transform-origin: 50px 45px;
            animation: ${speaking ? 'talkMouth 0.25s infinite alternate' : 'none'};
          }
          .head-bob {
            transform-origin: 50px 50px;
            animation: ${speaking ? 'bobHead 1.5s infinite alternate ease-in-out' : 'none'};
          }
          @keyframes pointArm {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-25deg); }
          }
          @keyframes talkMouth {
            0% { transform: scaleY(1); }
            100% { transform: scaleY(0.1); }
          }
          @keyframes bobHead {
            0% { transform: translateY(0); }
            100% { transform: translateY(-3px) rotate(2deg); }
          }
        `}</style>
        
        {/* Left Arm (Pointing) */}
        <g className="arm-point">
          <path d="M 35 60 L 5 45" stroke="#fcd34d" strokeWidth="7" strokeLinecap="round" />
          <path d="M 35 60 L 20 54" stroke="var(--accent-teal)" strokeWidth="8" strokeLinecap="round" />
        </g>
        
        {/* Right Arm (Resting) */}
        <path d="M 65 60 L 75 75" stroke="var(--accent-teal)" strokeWidth="7" strokeLinecap="round" />
        <circle cx="75" cy="75" r="3.5" fill="#fcd34d" />

        {/* Body */}
        <rect x="33" y="52" width="34" height="48" rx="12" fill="var(--accent-teal)" />
        <path d="M 50 52 L 50 100" stroke="rgba(0,0,0,0.1)" strokeWidth="2" />
        
        {/* Head Group */}
        <g className="head-bob">
          <circle cx="50" cy="34" r="17" fill="#fcd34d" /> {/* Skin tone */}
          {/* Hair */}
          <path d="M 30 35 Q 50 8 70 35 Q 75 22 50 15 Q 25 22 30 35" fill="#451a03" />
          {/* Eyes */}
          <circle cx="43" cy="31" r="2.5" fill="#1e293b" />
          <circle cx="57" cy="31" r="2.5" fill="#1e293b" />
          {/* Glasses */}
          <rect x="38" y="28" width="10" height="6" rx="2" fill="none" stroke="#0f172a" strokeWidth="1.5" />
          <rect x="52" y="28" width="10" height="6" rx="2" fill="none" stroke="#0f172a" strokeWidth="1.5" />
          <line x1="48" y1="31" x2="52" y2="31" stroke="#0f172a" strokeWidth="1.5" />
          
          {/* Mouth */}
          {speaking ? (
            <ellipse className="mouth-talk" cx="50" cy="43" rx="3.5" ry="5" fill="#991b1b" />
          ) : (
            <path d="M 46 43 Q 50 47 54 43" stroke="#991b1b" strokeWidth="2" fill="none" strokeLinecap="round" />
          )}
        </g>
      </svg>
    </div>
  )
}

export default function VoiceNarrator({ text, title = "Listen to AI Coach", compact = false }: VoiceNarratorProps) {
  const [speaking, setSpeaking] = useState(false)
  const [paused, setPaused] = useState(false)
  const [supported, setSupported] = useState(true)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setSupported(false)
      return
    }

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const startSpeaking = () => {
    if (!supported || !window.speechSynthesis) return

    window.speechSynthesis.cancel()

    // Clean text for clearer speech
    const cleanText = text
      .replace(/[#*_`]/g, '')
      .replace(/[\n\r]+/g, '. ')
      .replace(/spm/gi, 'steps per minute')
      .replace(/ms\b/g, 'milliseconds')
      .replace(/deg\b/g, 'degrees')

    const utter = new SpeechSynthesisUtterance(cleanText)
    utter.rate = 0.95 // slightly natural paced
    utter.pitch = 1.05

    // Pick an English voice if available
    const voices = window.speechSynthesis.getVoices()
    const preferred = voices.find(v => (v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Neural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('David')))) || voices.find(v => v.lang.startsWith('en'))
    if (preferred) utter.voice = preferred

    utter.onstart = () => {
      setSpeaking(true)
      setPaused(false)
    }

    utter.onend = () => {
      setSpeaking(false)
      setPaused(false)
    }

    utter.onerror = () => {
      setSpeaking(false)
      setPaused(false)
    }

    utteranceRef.current = utter
    window.speechSynthesis.speak(utter)
  }

  const stopSpeaking = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    setSpeaking(false)
    setPaused(false)
  }

  const togglePause = () => {
    if (!window.speechSynthesis) return
    if (paused) {
      window.speechSynthesis.resume()
      setPaused(false)
    } else {
      window.speechSynthesis.pause()
      setPaused(true)
    }
  }

  if (!supported) return null

  if (compact) {
    return (
      <button
        onClick={speaking ? stopSpeaking : startSpeaking}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          background: speaking ? 'rgba(13,148,136,0.15)' : 'var(--accent-teal-bg)',
          border: '1px solid var(--accent-teal-border)',
          borderRadius: '8px',
          padding: '0.3rem 0.65rem',
          fontSize: '0.76rem',
          fontWeight: 600,
          color: 'var(--accent-teal-dark)',
          cursor: 'pointer',
          transition: 'all 0.15s',
        }}
        title={speaking ? "Stop voiceover" : "Listen to audio feedback"}
      >
        {speaking ? (
          <>
            <CoachAvatar speaking={true} size={20} />
            <span style={{ color: '#dc2626' }}>Stop Audio</span>
          </>
        ) : (
          <>
            <Volume2 size={14} color="var(--accent-teal-dark)" />
            <span>Voice Coach</span>
          </>
        )}
      </button>
    )
  }
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.6rem',
      background: speaking ? 'linear-gradient(135deg, rgba(13,148,136,0.15), rgba(240,253,250,0.9))' : 'var(--accent-teal-bg)',
      border: '1px solid var(--accent-teal-border)',
      borderRadius: '10px',
      padding: '0.45rem 0.9rem',
    }}>
      <CoachAvatar speaking={speaking} />
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.6rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-teal-dark)' }}>
            {title}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          {!speaking ? (
            <button
              onClick={startSpeaking}
              style={{
                background: 'var(--accent-teal)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                padding: '0.25rem 0.6rem',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
                boxShadow: '0 2px 6px rgba(13,148,136,0.2)'
              }}
            >
              <Volume2 size={14} /> Play Voiceover
            </button>
          ) : (
            <>
              <button
                onClick={togglePause}
                style={{
                  background: '#ffffff',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  padding: '0.25rem 0.5rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                {paused ? <Play size={13} fill="currentColor" /> : <Pause size={13} />} {paused ? 'Resume' : 'Pause'}
              </button>
              <button
                onClick={stopSpeaking}
                style={{
                  background: 'rgba(239,68,68,0.1)',
                  border: '1px solid rgba(239,68,68,0.3)',
                  borderRadius: '6px',
                  padding: '0.25rem 0.5rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  color: '#dc2626',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                <VolumeX size={13} /> Stop
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
