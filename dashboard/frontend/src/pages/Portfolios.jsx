import { useApi, fmt, fmtPct } from '../lib/api'

// Note: Full pre-computation needs backend job; this shows politician activity ranking
// For full return computation, use the Politicians detail page

export default function Portfolios() {
  const { data: pols, loading } = useApi('/api/politicians')

  const sorted = (pols || [])
    .filter(p => p.trades >= 3)
    .sort((a, b) => b.buy_vol - a.buy_vol)

  return (
    <div>
      <div className="card card-sm" style={{ marginBottom: 16, background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)' }}>
        <div style={{ fontSize: 13, color: 'var(--accent)' }}>
          💡 Für vollständige Renditeberechnung: Politiker im Tab <strong>Politiker</strong> auswählen → Zeitraum setzen → Berechnen.
          Die Renditen werden direkt aus Yahoo Finance berechnet und berücksichtigen die tatsächlichen Haltezeiten.
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
          <div className="section-title">💼 Politiker-Rangliste — nach Handelsvolumen</div>
          <div className="hint">Für Renditeberechnung: Politiker anklicken → Portfolio-Detail öffnet sich</div>
        </div>
        {loading
          ? <div className="loading">Lade …</div>
          : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Politiker</th>
                  <th>Kammer</th>
                  <th>Trades</th>
                  <th>Käufe</th>
                  <th>Verkäufe</th>
                  <th>Kaufvolumen (ca.)</th>
                  <th>Letzter Trade</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((p, i) => (
                  <tr key={p.name}>
                    <td style={{ color: 'var(--text3)', fontVariantNumeric: 'tabular-nums' }}>{i+1}</td>
                    <td className="primary">{p.name}</td>
                    <td><span className="tag">{p.chamber}</span></td>
                    <td>{p.trades}</td>
                    <td style={{ color: 'var(--green)' }}>{p.buys}</td>
                    <td style={{ color: 'var(--red)'  }}>{p.sells}</td>
                    <td className="mono">{fmt(p.buy_vol)}</td>
                    <td className="mono" style={{ color: 'var(--text3)' }}>{p.last_trade}</td>
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
