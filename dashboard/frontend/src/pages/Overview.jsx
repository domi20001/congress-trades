import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi, fmt, fmtPct, logoUrl } from '../lib/api'
import { ReturnBar, PriceChart } from '../components/Charts'
import Logo from '../components/Logo'
import { TrendingUp, TrendingDown, AlertTriangle, Clock } from 'lucide-react'

function StatCard({ label, value, sub, color }) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${color || ''}`}>{value}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  )
}

export default function Overview() {
  const navigate = useNavigate()
  const { data: summary } = useApi('/api/summary')
  const { data: signals  } = useApi('/api/signals', { days: 21, min_pols: 2, limit: 5 })
  const { data: topStocks} = useApi('/api/top_stocks', { limit: 8 })
  const { data: pols     } = useApi('/api/politicians')

  const top5pols = pols?.slice(0, 5) || []
  const buyRate  = summary
    ? Math.round(summary.buys / (summary.buys + summary.sells) * 100)
    : null

  return (
    <div>
      {/* KPIs */}
      <div className="metrics">
        <StatCard label="Trades gesamt"  value={summary?.total?.toLocaleString('de') ?? '—'} sub={`Stand: ${summary?.latest_date ?? '…'}`} />
        <StatCard label="Politiker"      value={summary?.politicians ?? '—'}  sub="aktive Trader" />
        <StatCard label="Käufe"          value={summary?.buys?.toLocaleString('de') ?? '—'} color="green" sub={buyRate ? `${buyRate}% aller Trades` : ''} />
        <StatCard label="Verkäufe"       value={summary?.sells?.toLocaleString('de') ?? '—'} color="red"  sub={`${summary?.tickers ?? '—'} verschiedene Ticker`} />
      </div>

      <div className="grid-2" style={{ gap: 16 }}>
        {/* Kaufsignale */}
        <div className="card" style={{ padding: 0 }}>
          <div className="flex-between" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
            <div>
              <div className="section-title" style={{ marginBottom: 2 }}>🚨 Aktuelle Kaufsignale</div>
              <div className="hint">Letzten 21 Tage · ≥2 Politiker</div>
            </div>
            <button className="btn btn-ghost" style={{ fontSize: 12 }}
              onClick={() => navigate('/signals')}>Alle →</button>
          </div>
          {!signals
            ? <div className="loading">Lade …</div>
            : signals.length === 0
              ? <div className="empty" style={{ margin: 16 }}>Keine Signale</div>
              : signals.map(sig => (
                <div key={sig.ticker} className="signal-row"
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/signals`)}
                >
                  <Logo ticker={sig.ticker} size={28} />
                  <div className="signal-ticker">{sig.ticker}</div>
                  <div className="signal-name">{sig.name}</div>
                  <div className="signal-score-block">
                    <div className="score-bar-track">
                      <div className="score-bar-fill" style={{
                        width: `${sig.score}%`,
                        background: sig.label==='stark' ? 'var(--green)' : sig.label==='mittel' ? 'var(--amber)' : 'var(--text3)'
                      }} />
                    </div>
                    <span style={{ fontSize: 11, color: 'var(--text3)', minWidth: 28 }}>{sig.score.toFixed(0)}</span>
                  </div>
                  <span className={`badge badge-${sig.label}`}>{sig.label}</span>
                </div>
              ))
          }
        </div>

        {/* Top Politiker */}
        <div className="card" style={{ padding: 0 }}>
          <div className="flex-between" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
            <div>
              <div className="section-title" style={{ marginBottom: 2 }}>👤 Aktivste Politiker</div>
              <div className="hint">Nach Anzahl Trades</div>
            </div>
            <button className="btn btn-ghost" style={{ fontSize: 12 }}
              onClick={() => navigate('/politicians')}>Alle →</button>
          </div>
          {!pols
            ? <div className="loading">Lade …</div>
            : top5pols.map((p, i) => (
              <div key={p.name} className="portfolio-rank-row"
                onClick={() => navigate(`/politicians`)}>
                <div className="rank-num">{i + 1}</div>
                <div>
                  <div className="rank-name">{p.name}</div>
                  <div className="rank-chamber">{p.chamber}</div>
                </div>
                <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{p.trades} Trades</div>
                  <div style={{ fontSize: 11, color: 'var(--text3)' }}>
                    <span style={{ color: 'var(--green)' }}>{p.buys}↑</span>
                    {' '}<span style={{ color: 'var(--red)' }}>{p.sells}↓</span>
                  </div>
                </div>
              </div>
            ))
          }
        </div>
      </div>

      {/* Top Aktien */}
      <div className="card mt-16" style={{ padding: 0 }}>
        <div className="flex-between" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
          <div>
            <div className="section-title" style={{ marginBottom: 2 }}>📈 Meistgehandelte Aktien</div>
            <div className="hint">Alle Trades · nach Aktivität</div>
          </div>
          <button className="btn btn-ghost" style={{ fontSize: 12 }}
            onClick={() => navigate('/top-stocks')}>Alle →</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Ticker</th>
                <th>Unternehmen</th>
                <th>Trades</th>
                <th>Käufe</th>
                <th>Verkäufe</th>
                <th>Kaufanteil</th>
                <th>Volumen (ca.)</th>
              </tr>
            </thead>
            <tbody>
              {!topStocks
                ? <tr><td colSpan={8} className="loading">Lade …</td></tr>
                : topStocks.map(s => (
                  <tr key={s.ticker}>
                    <td><Logo ticker={s.ticker} size={24} /></td>
                    <td className="mono primary">{s.ticker}</td>
                    <td>{s.name || '—'}</td>
                    <td>{s.trades}</td>
                    <td style={{ color: 'var(--green)' }}>{s.buys}</td>
                    <td style={{ color: 'var(--red)' }}>{s.sells}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div className="score-bar-track" style={{ width: 60 }}>
                          <div className="score-bar-fill"
                            style={{ width: `${s.buy_pct}%`, background: s.buy_pct > 50 ? 'var(--green)' : 'var(--red)' }} />
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--text3)' }}>{s.buy_pct}%</span>
                      </div>
                    </td>
                    <td>{fmt(s.total_vol)}</td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
