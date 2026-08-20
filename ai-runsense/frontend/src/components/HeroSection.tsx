import { useRef, useEffect } from 'react'
import { Play, ArrowRight, Sparkles, TrendingUp, ChevronDown } from 'lucide-react'

interface HeroSectionProps {
  onGetStarted: () => void
  onExploreEvolution?: () => void
  userLoggedIn?: boolean
  videoSrc?: string
  posterSrc?: string
}

export default function HeroSection({
  onGetStarted,
  onExploreEvolution,
  userLoggedIn = false,
  videoSrc = '/videos/running-hero.mp4',
  posterSrc = '/videos/hero-poster.jpg',
}: HeroSectionProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    // Guarantee autoplay even on strict browser power policies
    const vid = videoRef.current
    if (vid) {
      vid.muted = true
      vid.defaultMuted = true
      const playPromise = vid.play()
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          // Autoplay was prevented; fallback poster image handles visual presentation
        })
      }
    }
  }, [videoSrc])

  return (
    <section
      style={{
        position: 'relative',
        width: '100%',
        height: '100vh',
        minHeight: '650px',
        maxHeight: '1080px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        background: '#090d16',
      }}
    >
      {/* ── Background Video Layer ── */}
      <video
        ref={videoRef}
        autoPlay
        muted
        loop
        playsInline
        poster={posterSrc}
        preload="auto"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: '68% center', // Focuses visual weight on runner on center-right
          zIndex: 1,
          opacity: 0.88,
          filter: 'contrast(1.08) brightness(0.92) saturate(1.1)',
        }}
      >
        <source src={videoSrc} type="video/mp4" />
      </video>

      {/* ── Cinematic Multi-Layer Gradient Overlays ── */}
      {/* Left heavy gradient: guarantees flawless white text readability */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: `linear-gradient(
            to right,
            rgba(6, 11, 21, 0.94) 0%,
            rgba(6, 11, 21, 0.88) 32%,
            rgba(8, 15, 28, 0.65) 55%,
            rgba(8, 15, 28, 0.25) 80%,
            rgba(8, 15, 28, 0.45) 100%
          )`,
          zIndex: 2,
          pointerEvents: 'none',
        }}
      />

      {/* Top & Bottom vignette: softens transitions into navigation and following sections */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: `linear-gradient(
            to bottom,
            rgba(5, 9, 18, 0.7) 0%,
            rgba(5, 9, 18, 0) 18%,
            rgba(5, 9, 18, 0) 75%,
            rgba(6, 11, 21, 0.95) 100%
          )`,
          zIndex: 3,
          pointerEvents: 'none',
        }}
      />

      {/* Subtle sports-tech teal ambient glow in bottom-left */}
      <div
        style={{
          position: 'absolute',
          bottom: '-10%',
          left: '-5%',
          width: '550px',
          height: '550px',
          background: 'radial-gradient(circle, rgba(13, 148, 136, 0.22) 0%, rgba(13, 148, 136, 0) 70%)',
          zIndex: 3,
          pointerEvents: 'none',
          filter: 'blur(30px)',
        }}
      />

      {/* ── Hero Foreground Content ── */}
      <div
        style={{
          position: 'relative',
          zIndex: 4,
          maxWidth: '1240px',
          width: '100%',
          margin: '0 auto',
          padding: '0 2.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        <div style={{ maxWidth: '680px' }}>
          {/* Badge */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.45rem',
              background: 'rgba(13, 148, 136, 0.2)',
              border: '1px solid rgba(20, 184, 166, 0.4)',
              backdropFilter: 'blur(12px)',
              padding: '0.35rem 0.95rem',
              borderRadius: '100px',
              marginBottom: '1.5rem',
              boxShadow: '0 0 20px rgba(13, 148, 136, 0.25)',
            }}
          >
            <Sparkles size={15} color="#2dd4bf" />
            <span
              style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#5eead4',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              AI Computer Vision · 15-Stage Biomechanics
            </span>
          </div>

          {/* Heading */}
          <h1
            style={{
              fontSize: 'clamp(2.5rem, 5.2vw, 4.2rem)',
              fontWeight: 900,
              lineHeight: 1.08,
              letterSpacing: '-0.03em',
              color: '#ffffff',
              marginBottom: '1.35rem',
              fontFamily: "'Space Grotesk', 'Inter', sans-serif",
              textShadow: '0 2px 20px rgba(0,0,0,0.6)',
            }}
          >
            Master your <br />
            <span
              style={{
                background: 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 40%, #fbbf24 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                display: 'inline-block',
              }}
            >
              running mechanics
            </span>{' '}
            with neural AI.
          </h1>

          {/* Description */}
          <p
            style={{
              fontSize: 'clamp(0.98rem, 1.3vw, 1.15rem)',
              color: 'rgba(241, 245, 249, 0.88)',
              lineHeight: 1.65,
              marginBottom: '2.5rem',
              maxWidth: '560px',
              fontWeight: 400,
              textShadow: '0 2px 10px rgba(0,0,0,0.5)',
            }}
          >
            Upload any running video from your phone or treadmill. Our neural pipeline analyzes cadence
            rhythm, vertical oscillation, braking load, and fatigue onset with frame-by-frame replay.
          </p>

          {/* Action CTAs */}
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <button
              onClick={onGetStarted}
              style={{
                background: 'linear-gradient(135deg, #0d9488 0%, #0f766e 100%)',
                border: '1px solid rgba(45, 212, 191, 0.5)',
                color: '#ffffff',
                fontSize: '1.02rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                padding: '0.95rem 2.25rem',
                borderRadius: '12px',
                cursor: 'pointer',
                boxShadow: '0 6px 28px rgba(13, 148, 136, 0.45), inset 0 1px 1px rgba(255,255,255,0.25)',
                transition: 'all 0.22s ease',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 10px 36px rgba(13, 148, 136, 0.6), inset 0 1px 1px rgba(255,255,255,0.3)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 6px 28px rgba(13, 148, 136, 0.45), inset 0 1px 1px rgba(255,255,255,0.25)'
              }}
            >
              <Play size={18} fill="white" />
              {userLoggedIn ? 'Analyze a Run' : 'Get Started Free'}
            </button>

            {onExploreEvolution && (
              <button
                onClick={onExploreEvolution}
                style={{
                  background: 'rgba(15, 23, 42, 0.65)',
                  border: '1px solid rgba(255, 255, 255, 0.18)',
                  backdropFilter: 'blur(16px)',
                  color: '#ffffff',
                  fontSize: '1.02rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.95rem 1.85rem',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.22s ease',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = 'rgba(30, 41, 59, 0.85)'
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.35)'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = 'rgba(15, 23, 42, 0.65)'
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.18)'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                <TrendingUp size={17} color="#2dd4bf" />
                Explore Trends
                <ArrowRight size={16} color="rgba(255,255,255,0.7)" />
              </button>
            )}
          </div>

          {/* Quick trust metrics row */}
          <div
            style={{
              display: 'flex',
              gap: '2rem',
              marginTop: '3.25rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid rgba(255, 255, 255, 0.12)',
              flexWrap: 'wrap',
            }}
          >
            <div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#ffffff', lineHeight: 1 }}>
                33 Keypoints
              </div>
              <div style={{ fontSize: '0.78rem', color: 'rgba(255, 255, 255, 0.6)', marginTop: '0.3rem' }}>
                Spatial Pose Tracking
              </div>
            </div>
            <div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2dd4bf', lineHeight: 1 }}>
                ±1.5s
              </div>
              <div style={{ fontSize: '0.78rem', color: 'rgba(255, 255, 255, 0.6)', marginTop: '0.3rem' }}>
                Timestamp Flaw Replay
              </div>
            </div>
            <div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#fbbf24', lineHeight: 1 }}>
                100%
              </div>
              <div style={{ fontSize: '0.78rem', color: 'rgba(255, 255, 255, 0.6)', marginTop: '0.3rem' }}>
                Automated Gait Analysis
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Subtle bottom scroll hint */}
      <div
        style={{
          position: 'absolute',
          bottom: '1.25rem',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.2rem',
          color: 'rgba(255, 255, 255, 0.4)',
          fontSize: '0.72rem',
          fontWeight: 500,
          pointerEvents: 'none',
        }}
      >
        <span>SCROLL TO EXPLORE</span>
        <ChevronDown size={14} className="float-anim" />
      </div>
    </section>
  )
}
