import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../services/api'
import { FiZap } from 'react-icons/fi'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()
  const submit = async (e) => {
    e.preventDefault(); setError(''); setBusy(true)
    try { await login(username, password); onLogin(); navigate('/') }
    catch { setError('Could not sign in. Check your username/password and confirm the Django API is running.') }
    finally { setBusy(false) }
  }
  return <div className="auth-page"><div className="auth-art"><div className="brand auth-brand"><div className="brand-mark"><FiZap /></div><div><strong>bizflow</strong><small>BUSINESS OS</small></div></div><div className="auth-art-copy"><span className="eyebrow">YOUR BUSINESS, IN SYNC</span><h1>Make every<br/>move <i>count.</i></h1><p>One clear view of your sales, stock and business performance.</p><div className="auth-mini-stats"><div><b>01</b><span>Understand<br/>your numbers</span></div><div><b>02</b><span>Stay ahead of<br/>your inventory</span></div><div><b>03</b><span>Grow with<br/>confidence</span></div></div></div><div className="auth-art-foot">BUILT FOR AMBITIOUS SMALL BUSINESSES</div></div><div className="auth-form-wrap"><form className="auth-form" onSubmit={submit}><div className="eyebrow">WELCOME BACK</div><h2>Sign in to BizFlow</h2><p className="muted">Enter your details to access your workspace.</p>{error && <div className="alert alert-danger py-2">{error}</div>}<label>Username</label><input className="form-control auth-input" value={username} onChange={e=>setUsername(e.target.value)} required autoComplete="username" placeholder="Your username"/><label>Password</label><input className="form-control auth-input" type="password" value={password} onChange={e=>setPassword(e.target.value)} required autoComplete="current-password" placeholder="Your password"/><button className="btn btn-primary w-100 auth-submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in →'}</button><div className="auth-switch">New to BizFlow? <Link to="/register">Create an account</Link></div><div className="auth-note">Your business data is accessed through the secured Django API.</div></form></div></div>
}
