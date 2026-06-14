import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, BarChart, Bar, ReferenceLine } from 'recharts'

export function SparkLine({ data, color = '#3b82f6', height = 48 }) {
  if (!data?.length) return null
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <Line type="monotone" dataKey="close" stroke={color} strokeWidth={1.5} dot={false} />
        <Tooltip
          contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
          labelStyle={{ color: 'var(--text3)' }}
          itemStyle={{ color }}
          formatter={v => [`$${v.toFixed(2)}`, 'Kurs']}
          labelFormatter={l => l}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function PriceChart({ data, tickers = [], height = 260 }) {
  if (!data || Object.keys(data).length === 0) return <div className="empty">Keine Kursdaten</div>

  // Merge all ticker series into one array by date
  const dateMap = {}
  for (const [tk, series] of Object.entries(data)) {
    for (const { date, value } of series) {
      if (!dateMap[date]) dateMap[date] = { date }
      dateMap[date][tk] = value
    }
  }
  const merged = Object.values(dateMap).sort((a, b) => a.date < b.date ? -1 : 1)

  const colors = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#8b5cf6','#06b6d4']

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={merged} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: 'var(--text3)' }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 10, fill: 'var(--text3)' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `${v.toFixed(0)}`}
          width={36}
        />
        <Tooltip
          contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
          labelStyle={{ color: 'var(--text3)' }}
          formatter={(v, name) => [`${v?.toFixed(1)}`, name]}
        />
        {Object.keys(data).map((tk, i) => (
          <Line key={tk} type="monotone" dataKey={tk}
            stroke={colors[i % colors.length]} strokeWidth={1.8}
            dot={false} connectNulls />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

export function ReturnBar({ data, height = 220 }) {
  if (!data?.length) return <div className="empty">Keine Daten</div>
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 40 }}>
        <XAxis dataKey="name" tick={{ fontSize: 9, fill: 'var(--text3)' }}
          interval={0} angle={-40} textAnchor="end" tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 10, fill: 'var(--text3)' }}
          tickLine={false} axisLine={false}
          tickFormatter={v => `${v > 0 ? '+' : ''}${v.toFixed(0)}%`} width={40} />
        <Tooltip
          contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
          formatter={v => [`${v > 0 ? '+' : ''}${v.toFixed(1)}%`, 'Rendite']}
        />
        <ReferenceLine y={0} stroke="var(--border2)" />
        <Bar dataKey="value" radius={[3,3,0,0]}
          fill="#3b82f6"
          label={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function BuyVsSell({ buys, sells, height = 180 }) {
  const data = [{ buys, sells }]
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 16 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="x" hide />
        <Tooltip
          contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
        />
        <Bar dataKey="buys"  name="Käufe"    fill="#22c55e" radius={[3,0,0,3]} stackId="a" />
        <Bar dataKey="sells" name="Verkäufe" fill="#ef4444" radius={[0,3,3,0]} stackId="a" />
      </BarChart>
    </ResponsiveContainer>
  )
}
