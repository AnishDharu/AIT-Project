import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../services/api'
import { FiZap } from 'react-icons/fi'

export default function Register() {
  const [form, setForm] = useState({ username:'', email:'', password:'', business_name:'' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()
  const update = e => setForm({...form, [e.target.name]:e.target.value})
  const submit = async e => {
    e.preventDefault(); setError(''); setBusy(true)
    try { await register(form); navigate('/login') }
    catch (err) { const data = err.response?.data; setError(data ? JSON.stringify(data) : 'Registration failed. Check that the backend is running.') }
    finally { setBusy(false) }
  }
  return <div className="auth-page"><div className="auth-art"><div className="brand auth-brand"><div className="brand-mark"><FiZap /></div><div><strong>bizflow</strong><small>BUSINESS OS</small></div></div><div className="auth-art-copy"><span className="eyebrow">A CLEARER WAY TO WORK</span><h1>Good business<br/>starts with <i>clarity.</i></h1><p>Bring your everyday operations into one connected workspace.</p></div><div className="auth-art-foot">SALES · INVENTORY · INSIGHTS</div></div><div className="auth-form-wrap"><form className="auth-form" onSubmit={submit}><div className="eyebrow">GET STARTED</div><h2>Create your workspace</h2><p className="muted">Set up your owner account and business profile.</p>{error && <div className="alert alert-danger py-2 small">{error}</div>}<label>Business name</label><input className="form-control auth-input" name="business_name" value={form.business_name} onChange={update} required placeholder="e.g. Northstar Supplies"/><label>Username</label><input className="form-control auth-input" name="username" value={form.username} onChange={update} required autoComplete="username"/><label>Email</label><input className="form-control auth-input" name="email" type="email" value={form.email} onChange={update} required autoComplete="email"/><label>Password (minimum 8 characters)</label><input className="form-control auth-input" name="password" type="password" value={form.password} onChange={update} required minLength={8} autoComplete="new-password"/><button className="btn btn-primary w-100 auth-submit" disabled={busy}>{busy ? 'Creating…' : 'Create account →'}</button><div className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></div></form></div></div>
}
