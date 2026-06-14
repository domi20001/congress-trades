import { useState, useMemo } from 'react'
import { useApi } from '../lib/api'
import Logo from '../components/Logo'

export default function Trades() {
  const [search,   setSearch  ] = useState('')
  const [direction,setDir     ] = useState('')
  const [sortKey,  setSort    ] = useState('transaction_date')
  const [sortDir,  setSortDir ] = useState('desc')
  const [page,     setPage    ] = useState(0)
  const PAGE = 100

  const { data, loading } = useApi('/api/trades', {
    limit: 500, offset: 0,
    ...(direction ? { direction } : {}),
  })

  const trades = data?.trades || []
  const total  = data?.total  || 0

  const filtered = useMemo(() => {
    let t = trades
    if (search) {
      const q = search.toLowerCase()
      t = t.filter(r =>
        r.politician?.toLowerCase().includes(q) ||
        r.ticker?.toLowerCase().includes(q) ||
        r.asset?.toLowerCase().includes(q)
      )
    }
    t = [...t].sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      return sortDir === 'asc'
        ? av < bv ? -1 : av > bv ? 1 : 0
        : av > bv ? -1 : av < bv ? 1 : 0
    })
    return t
  }, [trades, search, sortKey, sortDir])

  const paginated = filtered.slice(page * PAGE, (page + 1) * PAGE)
  const totalPages = Math.ceil(filtered.length / PAGE)

  function sort(key) {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSort(key); setSortDir('desc') }
  }
  function thClass(key) {
    return sortKey === key ? (sortDir === 'asc' ? 'sort-asc' : 'sort-desc') : ''
  }

  return (
    <div>
      {/* Filter bar */}
      <div className="card card-sm flex" style={{ gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <input className="input" placeholder="🔍  Suche Politiker, Ticker, Unternehmen …"
          style={{ flex: 1, minWidth: 200 }}
          value={search} onChange={e => { setSearch(e.target.value); setPage(0) }} />
        <select className="select" value={direction}
          onChange={e => { setDir(e.target.value); setPage(0) }}>
          <option value="">Kauf + Verkauf</option>
          <option value="Kauf">Nur Käufe</option>
          <option value="Verkauf">Nur Verkäufe</option>
        </select>
        <div style={{ fontSize: 12, color: 'var(--text3)', alignSelf: 'center' }}>
          {filtered.length.toLocaleString('de')} von {total.toLocaleString('de')} Trades
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading
          ? <div className="loading">Lade Trades …</div>
          : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th className={thClass('transaction_date')} onClick={() => sort('transaction_date')}>Datum</th>
                  <th className={thClass('politician')} onClick={() => sort('politician')}>Politiker</th>
                  <th>Kammer</th>
                  <th className={thClass('ticker')} onClick={() => sort('ticker')}>Ticker</th>
                  <th>Unternehmen</th>
                  <th className={thClass('direction')} onClick={() => sort('direction')}>Art</th>
                  <th className={thClass('amount_mid')} onClick={() => sort('amount_mid')}>Betrag (ca.)</th>
                  <th>Offenlegung</th>
                  <th>Quelle</th>
                </tr>
              </thead>
              <tbody>
                {paginated.map((t, i) => (
                  <tr key={i}>
                    <td><Logo ticker={t.ticker} size={22} /></td>
                    <td className="mono" style={{ color: 'var(--text3)' }}>{t.transaction_date}</td>
                    <td className="primary">{t.politician}</td>
                    <td><span className="tag">{t.chamber}</span></td>
                    <td className="mono primary">{t.ticker || '—'}</td>
                    <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {t.asset || '—'}
                    </td>
                    <td>
                      <span className={`badge badge-${t.direction === 'Kauf' ? 'buy' : 'sell'}`}>
                        {t.direction}
                      </span>
                    </td>
                    <td className="mono">
                      {t.amount_mid ? `$${Math.round(t.amount_mid).toLocaleString('de')}` : t.amount_range || '—'}
                    </td>
                    <td className="mono" style={{ color: 'var(--text3)' }}>{t.disclosure_date || '—'}</td>
                    <td>
                      {t.source_url
                        ? <a href={t.source_url} target="_blank" rel="noreferrer"
                            style={{ color: 'var(--accent)', fontSize: 12 }}>↗</a>
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex" style={{ gap: 8, padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
            <button className="btn btn-ghost" disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Zurück</button>
            <span style={{ fontSize: 12, color: 'var(--text3)', alignSelf: 'center' }}>
              Seite {page + 1} / {totalPages}
            </span>
            <button className="btn btn-ghost" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>Weiter →</button>
          </div>
        )}
      </div>
    </div>
  )
}
