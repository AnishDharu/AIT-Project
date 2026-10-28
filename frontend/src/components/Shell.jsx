import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { FiGrid, FiPackage, FiShoppingCart, FiUsers, FiTruck, FiCreditCard, FiBarChart2, FiLogOut, FiZap, FiCpu, FiClipboard } from 'react-icons/fi'
import { logout } from '../services/api'

const navItems = [
  { to: '/', label: 'Overview', icon: FiGrid, end: true },
  { to: '/products', label: 'Inventory', icon: FiPackage },
  { to: '/sales', label: 'Sales & Billing', icon: FiShoppingCart },
  { to: '/customers', label: 'Customers', icon: FiUsers },
  { to: '/suppliers', label: 'Suppliers', icon: FiTruck },
  { to: '/purchases', label: 'Purchases', icon: FiClipboard },
  { to: '/expenses', label: 'Expenses', icon: FiCreditCard },
  { to: '/analytics', label: 'Analytics', icon: FiBarChart2 },
  { to: '/intelligence', label: 'AI & Reports', icon: FiCpu },
]

export default function Shell({ children, user, setUser }) {
  const navigate = useNavigate()
  const handleLogout = () => {
    logout()
    setUser(null)
    navigate('/login')
  }
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><FiZap /></div><div><strong>bizflow</strong><small>BUSINESS OS</small></div></div>
      <div className="workspace"><span className="workspace-dot"></span><div><b>My Business</b><small>Owner workspace</small></div><span className="workspace-chevron">⌄</span></div>
      <div className="nav-caption">WORKSPACE</div>
      <nav className="side-nav">
        {navItems.map(item => <NavLink key={item.to} to={item.to} end={item.end} className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}><item.icon /><span>{item.label}</span>{item.label === 'Intelligence' && <em>NEW</em>}</NavLink>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="help-card"><div className="help-icon">✦</div><b>Make smarter moves</b><p>Turn daily business activity into clear next steps.</p><span>Explore insights ↗</span></div>
        <button className="logout-button" onClick={handleLogout}><FiLogOut /> Sign out</button>
        <div className="profile-mini"><div className="avatar">{(user?.username || 'U').slice(0,1).toUpperCase()}</div><div><b>{user?.username || 'Business Owner'}</b><small>Business owner</small></div><span className="profile-dots">•••</span></div>
      </div>
    </aside>
    <main className="main-panel">
      <header className="topbar"><div className="crumb">Workspace <span>/</span> <b>Business overview</b></div><div className="topbar-right"><span className="status-pill"><i></i> All systems operational</span><div className="top-avatar">{(user?.username || 'U').slice(0,1).toUpperCase()}</div></div></header>
      <div className="page-content">{children}</div>
      <footer className="footer-note">BizFlow <span>•</span> Smart business operations <span className="footer-right">MCA AIT Project · React + Django + MySQL</span></footer>
    </main>
  </div>
}
