import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

interface Props { score: number; components: Record<string, number> }

export default function EfficiencyGauge({ score, components }: Props) {
  if (score == null) return null

  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score }
  ]
  
  const getColor = (v: number) => v >= 80 ? '#059669' : v >= 60 ? '#d97706' : '#dc2626'
  const color = getColor(score)

  return (
    <div>
      <div style={{ position: 'relative', height: '220px', width: '100%', marginBottom: '1rem' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="75%"
              startAngle={180}
              endAngle={0}
              innerRadius="70%"
              outerRadius="90%"
              dataKey="value"
              stroke="none"
              cornerRadius={4}
            >
              <Cell fill={color} />
              <Cell fill="#e2e8f0" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        
        <div style={{ position: 'absolute', top: '55%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
          <p style={{ fontSize: '3rem', fontWeight: 900, lineHeight: 1, color }}>{score.toFixed(0)}</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>out of 100</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        {Object.entries(components || {}).slice(0, 6).map(([k, v]) => (
          <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem', borderBottom: '1px solid var(--border)', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{k.replace('_', ' ')}</span>
            <span style={{ fontWeight: 600, color: getColor(v) }}>{v.toFixed(0)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
