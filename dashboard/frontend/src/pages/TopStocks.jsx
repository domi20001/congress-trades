import { useState } from 'react'
import { useApi, useLazyApi, fmt } from '../lib/api'
import { PriceChart } from '../components/Charts'
import Logo from '../components/Logo'

const PERIODS = { '3 Monate':'3mo','6 Monate':'6mo','1 Jahr':'1y','2 Jahre':'2y','5 Jahre':'5y' }

export default function TopStocks() {
  const today = new Date().toISOString().slice(0,10)
  const [from, setFrom] = useState('2020-01-01')
  const [to,   setTo  ] = useState(today)
  const [limit, setLimit] = useState(20)
  const [selTickers, setSel] = useState([])
  const [period, setPeriod] = useState('1 Jahr')
  const [priceData, setPriceData] = useState({})
  const { fetch: fetchPrice } = useLazyApi()

  const { data: stocks, loading } = useApi('/api/top_stocks', { date_from: from, date_to: to, limit })

  async function loadPrices(tickers) {
    const per = PERIODS[period]
    const result = {}
    for (const tk of tickers) {
      const d = await fetchPrice(`/api/price_history/${tk}`, { period: per })
      if (d && !d.error && d.length > 1) {
        const base = d[0].close
        result[tk] = d.map(p => ({ date: p.date, value: +(p.close / base * 100).toFixed(2) }))
      }
    }
    setPriceData(result)
  }

  function toggleTicker(tk) {
    const next = selTickers.includes(tk)
      ? selTickers.filter(t => t !== tk)
      : [...selTickers, tk]
    setSel(next)
    loadPrices(next)
  }

  // Sort by buy pressure for indicator
  const sorted_pressure = [...(stocks || [])].sort((a,b) => b.buy_pct - a.buy_pct)

  return (
    <div>
      {/* Filters */}
      <div className="card card-sm flex" style={{ gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <label style={{ display:'flex', alignItems:'center', gap: 6, fontSize: 12 }}>
          <span style={{ color: 'var(--text3)' }}>Von</span>
          <input type="date" className="input" value={from} onChange={e => setFrom(e.target.value)} />
        </label>
        <label style={{ display:'flex', alignItems:'center', gap: 6, fontSize: 12 }}>
          <span style={{ color: 'var(--text3)' }}>Bis</span>
          <input type="date" className="input" value={to} onChange={e => setTo(e.target.value)} />
        </label>
        <label style={{ display:'flex', alignItems:'center', gap: 6, fontSize: 12 }}>
          <span style={{ color: 'var(--text3)' }}>Top</span>
          <select className="select" value={limit} onChange={e => setLimit(+e.target.value)}>
            {[10,20,30,50].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
      </div>

      <div className="grid-2" style={{ gap: 16, alignItems: 'start' }}>
        {/* Kaufdruck-Indikator */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
            <div className="section-title">🔥 Kaufdruck-Indikator</div>
            <div className="hint">Sortiert von meistgekauft → meistverkauft. Klicken = Kurschart.</div>
          </div>
          {loading
            ? <div className="loading">Lade …</div>
            : sorted_pressure.map(s => {
              const active = selTickers.includes(s.ticker)
              return (
                <div key={s.ticker}
                  className="signal-row"
                  style={{ cursor:'pointer', background: active ? 'var(--bg3)':undefined }}
                  onClick={() => toggleTicker(s.ticker)}
                >
                  <Logo ticker={s.ticker} size={28} />
                  <div style={{ minWidth: 56 }}>
                    <div className="signal-ticker">{s.ticker}</div>
                    <div style={{ fontSize:10, color:'var(--text3)' }}>{s.n_pols} Pol.</div>
                  </div>
                  <div style={{ flex:1, minWidth:0, fontSize:11, color:'var(--text3)',
                    overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                    {s.name}
                  </div>
                  {/* Buy/sell bar */}
                  <div style={{ display:'flex', alignItems:'center', gap:6, width:140 }}>
                    <div style={{ flex:1, height:8, borderRadius:4, background:'var(--bg3)', overflow:'hidden', display:'flex' }}>
                      <div style={{ width:`${s.buy_pct}%`, background:'var(--green)', height:'100%' }}/>
                      <div style={{ width:`${100-s.buy_pct}%`, background:'var(--red)', height:'100%' }}/>
                    </div>
                    <span style={{ fontSize:10, color:'var(--text3)', minWidth:32 }}>{s.buy_pct}%</span>
                  </div>
                  <div style={{ textAlign:'right', minWidth:56 }}>
                    <div style={{ fontSize:12, fontWeight:600, color:'var(--text)' }}>{fmt(s.total_vol)}</div>
                    <div style={{ fontSize:10, color:'var(--text3)' }}>{s.trades} Trades</div>
                  </div>
                </div>
              )
            })
          }
        </div>

        {/* Kurschart */}
        <div>
          <div className="card" style={{ padding:0, marginBottom:16 }}>
            <div className="flex-between" style={{ padding:'14px 20px', borderBottom:'1px solid var(--border)' }}>
              <div>
                <div className="section-title">📉 Kursverlauf (normiert)</div>
                <div className="hint">Aktie anklicken zum Ein-/Ausblenden</div>
              </div>
              <select className="select" value={period} onChange={e => { setPeriod(e.target.value); loadPrices(selTickers) }}>
                {Object.keys(PERIODS).map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div style={{ padding:'16px 20px' }}>
              {selTickers.length === 0
                ? <div className="empty">← Aktie anklicken</div>
                : <PriceChart data={priceData} height={260} />
              }
            </div>
          </div>

          {/* Detailtabelle */}
          <div className="card" style={{ padding:0 }}>
            <div style={{ padding:'12px 16px', borderBottom:'1px solid var(--border)' }}>
              <div className="section-title">📊 Detailtabelle</div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th></th><th>Ticker</th><th>Trades</th>
                    <th>Käufe</th><th>Verkäufe</th>
                    <th>Kaufvol.</th><th>Kaufanteil</th>
                  </tr>
                </thead>
                <tbody>
                  {(stocks||[]).map(s => (
                    <tr key={s.ticker}>
                      <td><Logo ticker={s.ticker} size={22} /></td>
                      <td className="mono primary">{s.ticker}</td>
                      <td>{s.trades}</td>
                      <td style={{ color:'var(--green)' }}>{s.buys}</td>
                      <td style={{ color:'var(--red)'  }}>{s.sells}</td>
                      <td className="mono">{fmt(s.buy_vol)}</td>
                      <td>
                        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                          <div className="score-bar-track" style={{ width:50 }}>
                            <div className="score-bar-fill" style={{ width:`${s.buy_pct}%`,
                              background: s.buy_pct>50?'var(--green)':'var(--red)' }}/>
                          </div>
                          <span style={{ fontSize:11, color:'var(--text3)' }}>{s.buy_pct}%</span>
                        </div>
                      </td>
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
