import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { type StyleDNA } from '../api/client'

interface Props { style: StyleDNA }

export default function StyleRadar({ style }: Props) {
  if (!style) return null

  const data = [
    { subject: 'Cadence', A: style.cadence, fullMark: 100 },
    { subject: 'Stride', A: style.stride, fullMark: 100 },
    { subject: 'Posture', A: style.posture, fullMark: 100 },
    { subject: 'Symmetry', A: style.symmetry, fullMark: 100 },
    { subject: 'Arm Swing', A: style.arm_swing, fullMark: 100 },
    { subject: 'Pelvic Stab.', A: style.pelvic_stability, fullMark: 100 },
    { subject: 'Rhythm', A: style.rhythm, fullMark: 100 },
    { subject: 'Vertical', A: style.vertical, fullMark: 100 },
  ]

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: '#ffffff', border: '1px solid var(--border)', padding: '0.5rem 0.75rem', borderRadius: '8px', fontSize: '0.8rem', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
          <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>{payload[0].payload.subject}</p>
          <p style={{ color: 'var(--accent-teal)' }}>Score: {payload[0].value}/100</p>
        </div>
      )
    }
    return null
  }

  return (
    <div style={{ position: 'relative' }}>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 11 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Radar name="Runner" dataKey="A" stroke="#0d9488" fill="#0d9488" fillOpacity={0.25} dot={{ r: 3, fill: '#0d9488' }} />
        </RadarChart>
      </ResponsiveContainer>
      
      <div style={{ textAlign: 'center', marginTop: '-10px' }}>
        <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Primary Classification</p>
        <p style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-teal-dark)' }}>{style.primary_style}</p>
        {style.secondary_style && (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>with elements of {style.secondary_style}</p>
        )}
      </div>
    </div>
  )
}
