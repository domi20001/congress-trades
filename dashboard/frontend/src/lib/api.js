import { useState, useEffect, useCallback } from 'react'

const BASE = import.meta.env.PROD
  ? 'https://congress-trades-api-znt7.onrender.com'
  : ''

export function useApi(path, params = {}) {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)

  const query = Object.keys(params).length
    ? '?' + new URLSearchParams(params).toString()
    : ''

  useEffect(() => {
    if (!path) return
    setLoading(true)
    setError(null)
    fetch(`${BASE}${path}${query}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [path + query])

  return { data, loading, error }
}

export function useLazyApi() {
  const [state, setState] = useState({ data: null, loading: false, error: null })

  const fetch_ = useCallback(async (path, params = {}) => {
    setState(s => ({ ...s, loading: true, error: null }))
    const query = Object.keys(params).length
      ? '?' + new URLSearchParams(params).toString()
      : ''
    try {
      const r = await fetch(`${BASE}${path}${query}`)
      const d = await r.json()
      setState({ data: d, loading: false, error: null })
      return d
    } catch (e) {
      setState({ data: null, loading: false, error: e.message })
      return null
    }
  }, [])

  return { ...state, fetch: fetch_ }
}

export function fmt(n, prefix = '$') {
  if (n == null || isNaN(n)) return '—'
  if (n >= 1_000_000) return `${prefix}${(n/1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `${prefix}${(n/1_000).toFixed(0)}K`
  return `${prefix}${n.toFixed(0)}`
}

export function fmtPct(n) {
  if (n == null || isNaN(n)) return '—'
  return `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`
}

export function logoUrl(ticker) {
  const map = {
    AAPL:'apple.com', MSFT:'microsoft.com', NVDA:'nvidia.com',
    GOOGL:'google.com', GOOG:'google.com', AMZN:'amazon.com',
    META:'meta.com', TSLA:'tesla.com', JPM:'jpmorganchase.com',
    V:'visa.com', MA:'mastercard.com', PLTR:'palantir.com',
    CRWD:'crowdstrike.com', AMD:'amd.com', INTC:'intel.com',
    ORCL:'oracle.com', IBM:'ibm.com', ADBE:'adobe.com',
    QCOM:'qualcomm.com', AVGO:'broadcom.com', MU:'micron.com',
    PYPL:'paypal.com', UBER:'uber.com', DASH:'doordash.com',
    ABNB:'airbnb.com', BKNG:'bookingholdings.com',
    AMGN:'amgen.com', PFE:'pfizer.com', MRK:'merck.com',
    LLY:'lilly.com', ABBV:'abbvie.com', JNJ:'jnj.com',
    UNH:'unitedhealthgroup.com', GS:'goldmansachs.com',
    MS:'morganstanley.com', BAC:'bankofamerica.com',
    WFC:'wellsfargo.com', BX:'blackstone.com', AXP:'americanexpress.com',
    LPLA:'lpl.com', BSX:'bostonscientific.com', ETN:'eaton.com',
    HON:'honeywell.com', GE:'ge.com', T:'att.com', VZ:'verizon.com',
    KO:'coca-cola.com', PEP:'pepsico.com', SBUX:'starbucks.com',
    MCD:'mcdonalds.com', ABT:'abbott.com', DDOG:'datadoghq.com',
    TTD:'thetradedesk.com', APP:'applovin.com', FLEX:'flex.com',
    FDS:'factset.com', VRSK:'verisk.com', ACN:'accenture.com',
  }
  const d = map[ticker?.toUpperCase()]
  return d ? `https://logo.clearbit.com/${d}?size=40` : null
}
