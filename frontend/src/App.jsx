import React, {useEffect, useState} from "react";
import {AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid} from "recharts";
import {Activity, AlertTriangle, MapPin, CloudRain, Waves, ShieldAlert, RefreshCw, Siren, CheckCircle2} from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
async function request(path, options={}) {
  const res = await fetch(`${API}${path}`, {headers:{"Content-Type":"application/json"}, ...options});
  if (!res.ok) throw new Error((await res.json()).detail || "API request failed");
  return res.json();
}
const fmt = n => Number(n ?? 0).toFixed(1);
function App(){
  const [data,setData]=useState(null), [alerts,setAlerts]=useState([]), [history,setHistory]=useState([]), [reports,setReports]=useState([]);
  const [busy,setBusy]=useState(false), [error,setError]=useState(""), [tab,setTab]=useState("Overview");
  const [form,setForm]=useState({name:"",phone:"",zone:"Zone A",description:""});
  async function load(){
    try { const [d,a,h,r]=await Promise.all([request("/api/dashboard"),request("/api/alerts"),request("/api/history?limit=35"),request("/api/sos")]); setData(d);setAlerts(a);setHistory(h);setReports(r);setError("");}
    catch(e){setError(e.message+" — start the FastAPI backend and check VITE_API_URL.");}
  }
  useEffect(()=>{load();const t=setInterval(load,5000);return()=>clearInterval(t)},[]);
  async function simulate(scenario){setBusy(true);try{await request("/api/simulate",{method:"POST",body:JSON.stringify({scenario})});await load()}catch(e){setError(e.message)}finally{setBusy(false)}}
  async function ack(id){try{await request(`/api/alerts/${id}/acknowledge`,{method:"POST"});await load()}catch(e){setError(e.message)}}
  async function submitSOS(e){e.preventDefault();try{await request("/api/sos",{method:"POST",body:JSON.stringify(form)});setForm({name:"",phone:"",zone:"Zone A",description:""});await load();alert("SOS report submitted.")}catch(e){setError(e.message)}}
  const zones=data?.zones||[];
  const riskColor = level => level==="CRITICAL"?"red":level==="HIGH"?"orange":level==="MODERATE"?"yellow":"green";
  return <div className="app">
    <aside className="sidebar"><div className="brand"><div className="logo"><Siren size={23}/></div><div><b>NagarAI</b><small>SMART CITY INTELLIGENCE</small></div></div>
      <div className="navlabel">WORKSPACE</div>{["Overview","Live Monitoring","Alerts","Citizen SOS","Analytics"].map((x,i)=><button className={`nav ${tab===x?"active":""}`} onClick={()=>setTab(x)} key={x}>{[<Activity/>,<Waves/>,<AlertTriangle/>,<ShieldAlert/>,<MapPin/>][i]}{x}</button>)}
      <div className="sidebottom"><span className="pulse"></span> SYSTEM ONLINE<small>Prototype environment</small></div>
    </aside>
    <main className="main"><header><div><div className="eyebrow">CITY EMERGENCY RESPONSE / FLOOD INTELLIGENCE</div><h1>{tab==="Overview"?"Emergency Command Center":tab}</h1><p>Monitor urban flood conditions and coordinate rapid response.</p></div><button className="refresh" onClick={load}><RefreshCw size={16}/> Refresh</button></header>
    {error&&<div className="error">{error}</div>}
    {tab==="Citizen SOS"?<section className="panel sos"><h2>Submit citizen emergency report</h2><p>Send an incident report to the NagarAI response dashboard.</p><form onSubmit={submitSOS}><label>Full name<input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label>Phone number<input required value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/></label><label>Zone<select value={form.zone} onChange={e=>setForm({...form,zone:e.target.value})}>{["Zone A","Zone B","Zone C"].map(z=><option>{z}</option>)}</select></label><label className="wide">Incident description<textarea required minLength="5" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label><button className="primary">Submit SOS report</button></form><h3>Recent citizen reports</h3>{reports.map(r=><div className="report" key={r.id}><b>#{r.id} · {r.zone}</b><span>{r.status}</span><p>{r.description}</p></div>)}</section>
    :tab==="Alerts"?<section className="panel"><h2>Emergency alerts</h2>{alerts.length===0?<p>No alerts currently recorded.</p>:alerts.map(a=><div className="alertrow" key={a.id}><AlertTriangle/><div><b>{a.level} · {a.zone}</b><p>{a.message}</p><small>{new Date(a.created_at).toLocaleString()}</small></div>{a.status==="ACTIVE"?<button onClick={()=>ack(a.id)}>Acknowledge</button>:<span className="muted"><CheckCircle2 size={15}/> Acknowledged</span>}</div>)}</section>
    :tab==="Analytics"?<section className="panel"><h2>Flood risk trend</h2><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={history}><CartesianGrid strokeDasharray="3 3" stroke="#263449"/><XAxis dataKey="timestamp" tickFormatter={v=>new Date(v).toLocaleTimeString()} stroke="#8190a5"/><YAxis domain={[0,100]} stroke="#8190a5"/><Tooltip labelFormatter={v=>new Date(v).toLocaleString()}/><Area type="monotone" dataKey="risk_score" stroke="#39c6a3" fill="#39c6a3" fillOpacity={.15}/></AreaChart></ResponsiveContainer></div></section>
    :<><section className="stats">
      <div className="stat"><span>OVERALL FLOOD RISK</span><strong className={riskColor(data?.overall_risk)}>{data?.overall_risk||"—"}</strong><small>Risk score: {data?.overall_score??"—"} / 100</small></div>
      <div className="stat"><span>ACTIVE ALERTS</span><strong>{data?.active_alerts??"—"}</strong><small>Requires response review</small></div>
      <div className="stat"><span>MONITORED ZONES</span><strong>{zones.length||"—"}</strong><small>Virtual IoT sensor network</small></div>
      <div className="stat"><span>LAST UPDATE</span><strong className="live">LIVE</strong><small>Auto-refresh every 5 seconds</small></div>
    </section>
    <section className="sectionhead"><div><h2>Live zone monitoring</h2><p>Virtual water-level and rainfall sensor telemetry</p></div><div className="simbuttons"><button disabled={busy} onClick={()=>simulate("normal")}>Normal</button><button disabled={busy} onClick={()=>simulate("heavy_rain")}>Simulate heavy rain</button><button disabled={busy} onClick={()=>simulate("rising_water")}>Rising water</button><button disabled={busy} onClick={()=>simulate("reset")}>Reset</button></div></section>
    <section className="zones">{zones.map(z=><article className="zone" key={z.zone}><div className="zonetop"><div><small>MONITORING AREA</small><h3>{z.zone}</h3></div><span className={`pill ${riskColor(z.risk_level)}`}>{z.risk_level}</span></div><div className="score">{z.risk_score}<small>/100 RISK</small></div><div className="meter"><i style={{width:`${z.risk_score}%`}}/></div><div className="metrics"><div><Waves/><span>Water level</span><b>{fmt(z.water_level_cm)} cm</b></div><div><CloudRain/><span>Rainfall</span><b>{fmt(z.rainfall_mm_hr)} mm/hr</b></div><div><Activity/><span>Rise rate</span><b>{fmt(z.rise_rate_cm_hr)} cm/hr</b></div></div><p className="recommend">{z.recommendation}</p></article>)}</section>
    <section className="bottomgrid"><div className="panel"><h2>Risk trend</h2><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={history}><CartesianGrid strokeDasharray="3 3" stroke="#263449"/><XAxis dataKey="timestamp" hide/><YAxis domain={[0,100]} stroke="#8190a5"/><Tooltip labelFormatter={v=>new Date(v).toLocaleString()}/><Area type="monotone" dataKey="risk_score" stroke="#39c6a3" fill="#39c6a3" fillOpacity={.15}/></AreaChart></ResponsiveContainer></div></div><div className="panel"><h2>Latest alerts</h2>{alerts.slice(0,4).map(a=><div className="miniAlert" key={a.id}><span className={`dot ${riskColor(a.level)}`}></span><div><b>{a.zone} · {a.level}</b><small>{a.status} · Score {a.score}</small></div></div>)}{alerts.length===0&&<p>No alerts yet.</p>}</div></section></>}
    <footer>NagarAI SOS · Emergency Intelligence Prototype <span>API: {API}</span></footer></main>
  </div>
}
export default App;
