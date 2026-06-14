import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import Sidebar    from './components/Sidebar'
import Overview   from './pages/Overview'
import Trades     from './pages/Trades'
import Signals    from './pages/Signals'
import Portfolios from './pages/Portfolios'
import Politicians from './pages/Politicians'
import TopStocks  from './pages/TopStocks'
import Delay      from './pages/Delay'

const PAGE_TITLES = {
  '/':           { title: 'Übersicht',     sub: 'US-Kongress Aktien-Transparenz' },
  '/trades':     { title: 'Alle Trades',   sub: 'Durchsuchbare Transaktionshistorie' },
  '/signals':    { title: 'Kaufsignal',    sub: 'Ungewöhnliche Kaufaktivität erkennen' },
  '/portfolios': { title: 'Portfolios',    sub: 'Rangliste nach Handelsvolumen' },
  '/politicians':{ title: 'Politiker',     sub: 'Portfolio & Rendite pro Person' },
  '/top-stocks': { title: 'Top-Aktien',   sub: 'Meistgehandelte Wertpapiere' },
  '/delay':      { title: 'Meldeverzug',   sub: 'Einhaltung der 45-Tage-Frist (STOCK Act)' },
}

function Header() {
  const loc = useLocation()
  const info = PAGE_TITLES[loc.pathname] || { title: '', sub: '' }
  return (
    <div className="topbar">
      <div>
        <div className="topbar-title">{info.title}</div>
        <div className="topbar-sub">{info.sub}</div>
      </div>
      <div className="topbar-right">
        <span style={{ fontSize: 11, color: 'var(--text3)' }}>
          Daten: STOCK Act · FMP API · Yahoo Finance
        </span>
      </div>
    </div>
  )
}

export default function App() {
  const [theme, setTheme] = useState(() =>
    localStorage.getItem('theme') || 'dark'
  )

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  function toggleTheme() {
    setTheme(t => t === 'dark' ? 'light' : 'dark')
  }

  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar theme={theme} onToggleTheme={toggleTheme} />
        <div className="main">
          <Header />
          <div className="content">
            <Routes>
              <Route path="/"            element={<Overview />} />
              <Route path="/trades"      element={<Trades />} />
              <Route path="/signals"     element={<Signals />} />
              <Route path="/portfolios"  element={<Portfolios />} />
              <Route path="/politicians" element={<Politicians />} />
              <Route path="/top-stocks"  element={<TopStocks />} />
              <Route path="/delay"       element={<Delay />} />
            </Routes>
          </div>
        </div>
      </div>
    </BrowserRouter>
  )
}
