import { useState, useEffect } from 'react'
import { useApi, useLazyApi, fmt } from '../lib/api'
import { PriceChart } from '../components/Charts'
import Logo from '../components/Logo'

const PERIODS = { '3 Monate': '3mo', '6 Monate': '6mo', '1 Jahr': '1y', '2 Jahre': '2y' }

export default function Signals() {
  const [days,    setDays   ] = useState(21)
  const [minPols, setMinPols] = useState(2)
  const [limit,   setLimit  ] = useState(10)
  const [selTickers, setSelTickers] = useState([])
  const [period,  setPeriod ] = useState('3 Monate')
  const [priceData, setPriceData] = useState({})
  const { fetch: fetchPrice, loading: priceLoading } = useLazyApi()

  const { data: signals, loading } = useApi('/api/signals', { days, min_pols: minPols, limit })

  // Auto-select top 3 when signals load
  useEffect(() => {
    if (signals?.length) setSelTickers(signals.slice(0,3).map(s => s.ticker))
  }, [signals])

  // Load price data when selection changes
  useEffect(() => {
    if (!selTickers.length) return
    const per = PERIODS[period]
    const load = async () => {
      const result = {}
      for (const tk of selTickers) {
        const d = await fetchPrice(`/api/price_history/${tk}`, { period: per })
        if (d && !d.error && d.length > 1) {
          const base = d[0].close
          result[tk] = d.map(p => ({ date: p.date, value: +(p.close / base * 100).toFixed(2) }))
        }
      }
      setPriceData(result)
    }
    load()
  }, [selTickers, period])

  function toggleTicker(tk) {
    setSelTickers(prev => prev.includes(tk) ? prev.filter(t => t !== tk) : [...prev, tk])
  }

  return (
    <div>
      {/* Controls */}
      <div className="card card-sm flex" style={{ gap: 20, marginBottom: 16, flexWrap: 'wrap' }}>
        <label style={{ display:'flex', alignItems:'center', gap: 8, fontSize: 13 }}>
          <span style={{ color: 'var(--text3)' }}>Fenster</span>
          <select className="select" value={days} onChange={e => setDays(+e.target.value)}>
            {[7,14,21,30,60,90].map(d => <option key={d} value={d}>{d} Tage</option>)}
          </select>
        </label>
        <label style={{ display:'flex', alignItems:'center', gap: 8, fontSize: 13 }}>
          <span style={{ color: 'var(--text3)' }}>Min. Politiker</span>
          <select className="select" value={minPols} onChange={e => setMinPols(+e.target.value)}>
            {[1,2,3,4].map(n => <option key={n} value={n}>{n}+</option>)}
          </select>
        </label>
        <label style={{ display:'flex', alignItems:'center', gap: 8, fontSize: 13 }}>
          <span style={{ color: 'var(--text3)' }}>Anzahl</span>
          <select className="select" value={limit} onChange={e => setLimit(+e.target.value)}>
            {[5,10,15,20].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
      </div>

      <div className="grid-2" style={{ gap: 16, alignItems: 'start' }}>
        {/* Signal list */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
            <div className="section-title">🚨 Kaufsignale — letzte {days} Tage</div>
            <div className="hint">Score: Anzahl Käufe (30%) + Diversität (30%) + Volumen (20%) + Beschleunigung (20%)</div>
          </div>
          {loading
            ? <div className="loading">Berechne Signale …</div>
            : !signals?.length
              ? <div className="empty" style={{ margin: 16 }}>Keine Signale mit ≥{minPols} Politikern im Fenster</div>
              : signals.map((sig, i) => {
                const active = selTickers.includes(sig.ticker)
                return (
                  <div key={sig.ticker}
                    className="signal-row"
                    style={{ cursor: 'pointer', background: active ? 'var(--bg3)' : undefined }}
                    onClick={() => toggleTicker(sig.ticker)}
                  >
                    <div style={{ color: 'var(--text3)', fontSize: 12, minWidth: 20 }}>{i+1}</div>
                    <Logo ticker={sig.ticker} size={30} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display:'flex', gap: 8, alignItems: 'center' }}>
                        <span className="signal-ticker">{sig.ticker}</span>
                        <span className={`badge badge-${sig.label}`}>{sig.label}</span>
                      </div>
                      <div className="signal-name">{sig.name}</div>
                    </div>
                    <div style={{ width: 140 }}>
                      <div style={{ display:'flex', alignItems:'center', gap: 6, marginBottom: 3 }}>
                        <div className="score-bar-track">
                          <div className="score-bar-fill" style={{
                            width: `${sig.score}%`,
                            background: sig.label==='stark' ? 'var(--green)' : sig.label==='mittel' ? 'var(--amber)' : 'var(--text3)'
                          }}/>
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--text3)' }}>{sig.score.toFixed(0)}/100</span>
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text3)' }}>
                        🛒 {sig.n_buys} Käufe &nbsp; 👥 {sig.n_pols} Pol.
                        {sig.accel > 0 && <span style={{ color: 'var(--green)' }}> ⚡+{sig.accel}</span>}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{fmt(sig.buy_vol)}</div>
                      <div style={{ fontSize: 10, color: 'var(--text3)' }}>Vol. Käufe</div>
                    </div>
                  </div>
                )
              })
          }
        </div>

        {/* Price chart */}
        <div>
          <div className="card" style={{ padding: 0 }}>
            <div className="flex-between" style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
              <div>
                <div className="section-title">📉 Kursverlauf (normiert = 100)</div>
                <div className="hint">Auf Signal-Aktie klicken um sie ein/auszublenden</div>
              </div>
              <select className="select" value={period} onChange={e => setPeriod(e.target.value)}>
                {Object.keys(PERIODS).map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div style={{ padding: '16px 20px' }}>
              {priceLoading
                ? <div className="loading">Lade Kursdaten …</div>
                : <PriceChart data={priceData} height={260} />
              }
            </div>
          </div>

          {/* Detail table */}
          <div className="card mt-16" style={{ padding: 0 }}>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
              <div className="section-title">📊 Detailtabelle</div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th></th><th>Ticker</th><th>Score</th>
                    <th>Käufe</th><th>Politiker</th>
                    <th>Volumen</th><th>Beschl.</th><th>Letzter Kauf</th>
                  </tr>
                </thead>
                <tbody>
                  {signals?.map(s => (
                    <tr key={s.ticker}>
                      <td><Logo ticker={s.ticker} size={22} /></td>
                      <td className="mono primary">{s.ticker}</td>
                      <td><span className={`badge badge-${s.label}`}>{s.score.toFixed(0)}</span></td>
                      <td>{s.n_buys}</td>
                      <td>{s.n_pols}</td>
                      <td>{fmt(s.buy_vol)}</td>
                      <td>{s.accel > 0 ? <span style={{ color: 'var(--green)' }}>+{s.accel}</span> : '—'}</td>
                      <td style={{ color: 'var(--text3)' }}>{s.last_buy}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
