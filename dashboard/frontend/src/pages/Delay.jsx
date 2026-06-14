import { useMemo } from 'react'
import { useApi } from '../lib/api'

export default function Delay() {
  const { data, loading } = useApi('/api/trades', { limit: 1000 })
  const trades = data?.trades || []

  const rows = useMemo(() => {
    return trades
      .filter(t => t.transaction_date && t.disclosure_date)
      .map(t => {
        const ms = new Date(t.disclosure_date) - new Date(t.transaction_date)
        return { ...t, delay: Math.round(ms / 86400000) }
      })
      .filter(t => t.delay >= 0)
      .sort((a, b) => b.delay - a.delay)
  }, [trades])

  const avg = rows.length ? Math.round(rows.reduce((s,r) => s + r.delay, 0) / rows.length) : 0
  const late = rows.filter(r => r.delay > 45).length

  return (
    <div>
      <div className="metrics" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 16 }}>
        <div className="metric">
          <div className="metric-label">Analysierte Trades</div>
          <div className="metric-value">{rows.length.toLocaleString('de')}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Ø Meldeverzug</div>
          <div className="metric-value">{avg} Tage</div>
          <div className="metric-sub">STOCK Act: max. 45 Tage</div>
        </div>
        <div className="metric">
          <div className="metric-label">Verspätet (&gt;45 Tage)</div>
          <div className={`metric-value ${late > 0 ? 'red' : 'green'}`}>{late}</div>
          <div className="metric-sub">{rows.length ? Math.round(late/rows.length*100) : 0}% der Trades</div>
        </div>
      </div>

      <div className="card" style={{ padding:0 }}>
        <div style={{ padding:'14px 20px', borderBottom:'1px solid var(--border)' }}>
          <div className="section-title">⏱️ Meldeverzug — sortiert nach Verzug (absteigend)</div>
        </div>
        {loading
          ? <div className="loading">Lade …</div>
          : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Politiker</th><th>Ticker</th>
                  <th>Transaktion</th><th>Offenlegung</th>
                  <th>Verzug (Tage)</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0,200).map((r,i) => (
                  <tr key={i}>
                    <td className="primary">{r.politician}</td>
                    <td className="mono">{r.ticker || '—'}</td>
                    <td className="mono" style={{ color:'var(--text3)' }}>{r.transaction_date}</td>
                    <td className="mono" style={{ color:'var(--text3)' }}>{r.disclosure_date}</td>
                    <td className="mono" style={{ fontWeight:600, color: r.delay>45?'var(--red)':r.delay>30?'var(--amber)':'var(--text)' }}>
                      {r.delay}
                    </td>
                    <td>
                      {r.delay > 45
                        ? <span className="badge badge-sell">Verspätet</span>
                        : <span className="badge badge-buy">Fristgerecht</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
