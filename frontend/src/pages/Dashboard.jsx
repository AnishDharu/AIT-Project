import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js'
import { FiArrowUpRight, FiArrowDownRight, FiPackage, FiDollarSign, FiTrendingUp, FiUsers, FiAlertTriangle, FiPlus, FiArrowRight } from 'react-icons/fi'
import api from '../services/api'
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const money = value => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(value || 0))
const Card = ({label,value,icon:Icon,tone,caption}) => <div className="metric-card"><div className="metric-top"><span>{label}</span><div className={`metric-icon ${tone}`}><Icon/></div></div><div className="metric-value">{value}</div><div className="metric-caption">{caption}</div></div>

export default function Dashboard({ user }) {
  const [summary,setSummary] = useState(null)
  const [chart,setChart] = useState([])
  const [products,setProducts] = useState([])
  const [sales,setSales] = useState([])
  const [error,setError] = useState('')
  const [loading,setLoading] = useState(true)
  useEffect(() => {
    let alive = true
    Promise.all([
      api.get('/dashboard/summary/'),
      api.get('/dashboard/sales-chart/'),
      api.get('/products/'),
      api.get('/sales/')
    ]).then(([s,c,p,sa]) => {
      if(!alive) return
      setSummary(s.data); setChart(c.data)
      setProducts(Array.isArray(p.data) ? p.data : (p.data.results || []))
      setSales(Array.isArray(sa.data) ? sa.data : [])
    }).catch(() => alive && setError('Unable to load live data. Confirm the Django server and MySQL connection, then sign in again.'))
      .finally(() => alive && setLoading(false))
    return () => { alive=false }
  },[])
  const chartData = { labels: chart.map(x=>x.month), datasets:[{label:'Revenue',data:chart.map(x=>Number(x.revenue)),backgroundColor:'#635bff',borderRadius:6,maxBarThickness:34}]}
  const chartOptions = { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}, scales:{x:{grid:{display:false},ticks:{color:'#8b91a3'}},y:{grid:{color:'#eff0f5'},ticks:{color:'#8b91a3',callback:v=>`₹${Number(v).toLocaleString('en-IN')}`}}}}
  const lowStock = products.filter(p=>Number(p.stock_quantity)<=Number(p.minimum_stock))
  return <div>
    <div className="welcome-row"><div><div className="eyebrow">MONDAY MINDSET, EVERY DAY</div><h1>Good to see you, {user?.username || 'there'} <span>✦</span></h1><p className="muted">Here's what's happening with your business today.</p></div><div className="welcome-actions"><Link className="btn btn-outline-secondary action-btn" to="/products"><FiPackage/> Manage stock</Link><Link className="btn btn-primary action-btn" to="/sales"><FiPlus/> New sale</Link></div></div>
    {error && <div className="alert alert-warning">{error}</div>}
    {loading && <div className="loading-line">Loading your business overview…</div>}
    <div className="section-heading"><div><h3>Business snapshot</h3><p>Performance for {summary?.period || 'the current month'}</p></div><span className="live-badge"><i></i> LIVE DATA</span></div>
    <div className="metrics-grid">
      <Card label="Monthly revenue" value={money(summary?.monthly_revenue)} icon={FiDollarSign} tone="violet" caption="Sales recorded this month"/>
      <Card label="Estimated net profit" value={money(summary?.estimated_net_profit)} icon={FiTrendingUp} tone="mint" caption="Revenue less COGS & expenses"/>
      <Card label="Products tracked" value={summary?.total_products ?? '—'} icon={FiPackage} tone="blue" caption="Active inventory items"/>
      <Card label="Low-stock items" value={summary?.low_stock_products ?? '—'} icon={FiAlertTriangle} tone="amber" caption="At or below minimum level"/>
    </div>
    <div className="dashboard-grid">
      <section className="panel chart-panel"><div className="panel-heading"><div><h3>Revenue overview</h3><p>Recorded sales grouped by month</p></div><span className="chart-period">HISTORY</span></div><div className="chart-wrap">{chart.length ? <Bar data={chartData} options={chartOptions}/> : <div className="empty-chart">Your revenue chart will appear when sales are recorded.</div>}</div></section>
      <section className="panel health-panel"><div className="panel-heading"><div><h3>Business pulse</h3><p>A quick read on operations</p></div><span className="pulse-spark">✦</span></div><div className="pulse-row"><div className="pulse-number">{summary ? Math.max(0,Math.min(100,Math.round(Number(summary.monthly_revenue)>0 ? (Number(summary.estimated_net_profit)/Number(summary.monthly_revenue))*100 : 0))) : '—'}<small>%</small></div><div><b>Profit margin</b><p>Estimated for {summary?.period || 'this month'}</p></div></div><div className="progress pulse-progress"><div className="progress-bar" style={{width:`${summary ? Math.max(0,Math.min(100,Math.round(Number(summary.monthly_revenue)>0 ? (Number(summary.estimated_net_profit)/Number(summary.monthly_revenue))*100 : 0))) : 0}%`}}/></div><div className="pulse-foot"><span>Monthly expenses</span><b>{money(summary?.monthly_expenses)}</b></div><div className="pulse-foot"><span>Customers</span><b>{summary?.total_customers ?? '—'}</b></div><div className="pulse-foot"><span>Suppliers</span><b>{summary?.total_suppliers ?? '—'}</b></div><div className="pulse-note">This is an indicative margin, not a credit score or formal financial rating.</div></section>
    </div>
    <div className="lower-grid">
      <section className="panel"><div className="panel-heading"><div><h3>Inventory watch</h3><p>Items that may need attention</p></div><Link to="/products" className="text-link">View inventory <FiArrowRight/></Link></div>
        {lowStock.length ? <div className="simple-list">{lowStock.slice(0,5).map(p=><div className="list-row" key={p.id}><div className="product-avatar">{p.name?.slice(0,1)}</div><div className="list-main"><b>{p.name}</b><small>SKU: {p.sku}</small></div><div className="stock-quantity"><b>{p.stock_quantity}</b><small>in stock</small></div><span className="warning-tag">Low stock</span></div>)}</div> : <div className="empty-state"><div className="empty-state-icon"><FiPackage/></div><b>Inventory looks healthy</b><p>No products are at or below their minimum stock level.</p></div>}
      </section>
      <section className="panel"><div className="panel-heading"><div><h3>Recent sales</h3><p>Your latest transactions</p></div><Link to="/sales" className="text-link">All sales <FiArrowRight/></Link></div>
        {sales.length ? <div className="simple-list">{sales.slice(0,5).map(s=><div className="list-row" key={s.id}><div className="sale-avatar">↗</div><div className="list-main"><b>{s.customer_name || 'Walk-in customer'}</b><small>{s.invoice_number}</small></div><div className="sale-amount"><b>{money(s.total_amount)}</b><small>{s.sale_date}</small></div><span className={`payment-tag ${s.payment_status?.toLowerCase()}`}>{s.payment_status}</span></div>)}</div> : <div className="empty-state"><div className="empty-state-icon"><FiDollarSign/></div><b>No sales yet</b><p>Create your first sale to see real transaction activity here.</p><Link to="/sales" className="text-link">Create a sale <FiArrowRight/></Link></div>}
      </section>
    </div>
  </div>
}
