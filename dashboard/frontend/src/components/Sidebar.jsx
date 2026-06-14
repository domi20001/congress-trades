import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, Users, Briefcase,
  AlertTriangle, BarChart2, Clock, Sun, Moon
} from 'lucide-react'

const nav = [
  { to: '/',           icon: LayoutDashboard, label: 'Übersicht' },
  { to: '/trades',     icon: BarChart2,       label: 'Alle Trades' },
  { to: '/signals',    icon: AlertTriangle,   label: 'Kaufsignal',  badge: 'NEU' },
  { to: '/portfolios', icon: Briefcase,       label: 'Portfolios' },
  { to: '/politicians',icon: Users,           label: 'Politiker' },
  { to: '/top-stocks', icon: TrendingUp,      label: 'Top-Aktien' },
  { to: '/delay',      icon: Clock,           label: 'Meldeverzug' },
]

export default function Sidebar({ theme, onToggleTheme }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🏛️</div>
        <div>
          <div className="sidebar-logo-text">Congress Trades</div>
          <div className="sidebar-logo-sub">STOCK Act · 2012</div>
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Navigation</div>
        {nav.map(({ to, icon: Icon, label, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon className="icon" size={15} />
            {label}
            {badge && <span className="nav-badge">{badge}</span>}
          </NavLink>
        ))}
      </div>

      <div className="sidebar-footer">
        <button className="theme-toggle" onClick={onToggleTheme}>
          {theme === 'dark'
            ? <><Sun size={13} /> Light Mode</>
            : <><Moon size={13} /> Dark Mode</>}
        </button>
      </div>
    </aside>
  )
}
