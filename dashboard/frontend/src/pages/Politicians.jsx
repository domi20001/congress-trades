import { useState } from 'react'
import { useApi, useLazyApi, fmt, fmtPct } from '../lib/api'
import Logo from '../components/Logo'

export default function Politicians() {
  const { data: pols, loading } = useApi('/api/politicians')
  const [sel, setSel]     = useState(null)
  const [dateFrom, setFrom] = useState('2020-01-01')
  const [dateTo,   setTo  ] = useState(new Date().toISOString().slice(0,10))
  const { data: port, loading: portLoading, fetch: fetchPort } = useLazyApi()
  const [search, setSearch] = useState('')

  function selectPol(name) {
    setSel(name)
    fetchPort(`/api/portfolio/${encodeURIComponent(name)}`, { date_from: dateFrom, date_to: dateTo })
  }

  function reload() {
    if (sel) fetchPort(`/api/portfolio/${encodeURIComponent(sel)}`, { date_from: dateFrom, date_to: dateTo })
  }

  const filtered = (pols || []).filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
  )

  const positions = port?.positions || []
  const withRet = positions.filter(p => p.rendite_pct != null)
  const totalInv = withRet.reduce((s, p) => s + (p.buy_vol || 0), 0)
  const wRet = totalInv > 0
    ? withRet.reduce((s, p) => s + (p.rendite_pct * p.buy_vol), 0) / totalInv
    : null

  return (
    <div className="grid-2" style={{ alignItems: 'start', gap: 16 }}>
      {/* Politiker-Liste */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)' }}>
          <div className="section-title">👤 Alle Politiker</div>
          <input className="input" placeholder="Suchen …" style={{ width: '100%', marginTop: 10 }}
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        {loading
          ? <div className="loading">Lade …</div>
          : <div style={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto' }}>
              {filtered.map((p, i) => (
                <div key={p.name}
                  className="portfolio-rank-row"
                  style={{ background: sel === p.name ? 'var(--bg3)' : undefined }}
                  onClick={() => selectPol(p.name)}
                >
                  <div className="rank-num">{i + 1}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="rank-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                    <div className="rank-chamber">{p.chamber}</div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{p.trades}</div>
                    <div style={{ fontSize: 10, color: 'var(--text3)' }}>
                      <span style={{ color: 'var(--green)' }}>{p.buys}↑</span>
                      {' '}<span style={{ color: 'var(--red)' }}>{p.sells}↓</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
        }
      </div>

      {/* Portfolio-Detail */}
      <div>
        {!sel
          ? <div className="empty">← Politiker auswählen</div>
          : (
          <div>
            {/* Zeitraum */}
            <div className="card card-sm flex" style={{ gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
              <label style={{ display:'flex', alignItems:'center', gap: 6, fontSize: 12 }}>
                <span style={{ color: 'var(--text3)' }}>Von</span>
                <input type="date" className="input" value={dateFrom}
                  onChange={e => setFrom(e.target.value)} />
              </label>
              <label style={{ display:'flex', alignItems:'center', gap: 6, fontSize: 12 }}>
                <span style={{ color: 'var(--text3)' }}>Bis</span>
                <input type="date" className="input" value={dateTo}
                  onChange={e => setTo(e.target.value)} />
              </label>
              <button className="btn btn-primary" onClick={reload}>Berechnen</button>
            </div>

            {/* Metriken */}
            {wRet != null && (
              <div className="metrics" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 12 }}>
                <div className="metric">
                  <div className="metric-label">Rendite (gewichtet)</div>
                  <div className={`metric-value ${wRet >= 0 ? 'green' : 'red'}`}>{fmtPct(wRet)}</div>
                </div>
                <div className="metric">
                  <div className="metric-label">Invest. Kapital</div>
                  <div className="metric-value">{fmt(totalInv)}</div>
                </div>
                <div className="metric">
                  <div className="metric-label">Gewinn/Verlust</div>
                  <div className={`metric-value ${totalInv * wRet / 100 >= 0 ? 'green' : 'red'}`}>
                    {fmt(Math.abs(totalInv * wRet / 100))}{totalInv * wRet / 100 < 0 ? ' (−)' : ''}
                  </div>
                </div>
              </div>
            )}

            {/* Positionen */}
            <div className="card" style={{ padding: 0 }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
                <div className="section-title">{sel} — Portfolio</div>
              </div>
              {portLoading
                ? <div className="loading">Berechne …</div>
                : positions.length === 0
                  ? <div className="empty" style={{ margin: 16 }}>Keine Positionen mit Ticker</div>
                  : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th></th><th>Ticker</th><th>Unternehmen</th>
                          <th>Status</th><th>Käufe</th><th>Verkäufe</th>
                          <th>Kaufvol.</th><th>Rendite</th><th>Gew./Verl.</th>
                          <th>Erster Kauf</th>
                        </tr>
                      </thead>
                      <tbody>
                        {positions.map(p => (
                          <tr key={p.ticker}>
                            <td><Logo ticker={p.ticker} size={22} /></td>
                            <td className="mono primary">{p.ticker}</td>
                            <td style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</td>
                            <td><span className={`badge badge-${p.is_open ? 'open' : 'close'}`}>{p.is_open ? 'Offen' : 'Geschlossen'}</span></td>
                            <td style={{ color: 'var(--green)' }}>{p.n_buys}</td>
                            <td style={{ color: 'var(--red)' }}>{p.n_sells}</td>
                            <td className="mono">{fmt(p.buy_vol)}</td>
                            <td className="mono" style={{ fontWeight: 600, color: p.rendite_pct > 0 ? 'var(--green)' : p.rendite_pct < 0 ? 'var(--red)' : 'var(--text3)' }}>
                              {p.rendite_pct != null ? fmtPct(p.rendite_pct) : '—'}
                            </td>
                            <td className="mono" style={{ color: p.gewinn_ca > 0 ? 'var(--green)' : p.gewinn_ca < 0 ? 'var(--red)' : 'var(--text3)' }}>
                              {p.gewinn_ca != null ? fmt(Math.abs(p.gewinn_ca)) : '—'}
                            </td>
                            <td className="mono" style={{ color: 'var(--text3)' }}>{p.first_buy}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              }
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
