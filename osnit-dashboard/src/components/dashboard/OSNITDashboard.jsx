import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import {
  XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar, ResponsiveContainer, AreaChart, Area
} from "recharts";

const INTEL = "http://127.0.0.1:8000/intelligence";
const INC   = "http://127.0.0.1:8000/incidents";
const OPS   = "http://127.0.0.1:8000/operations";

const TABS = ["Overview", "Intelligence", "Reports", "Explorer", "Operations"];

const SEV_COLOR = {
  critical: "#ff2d55",
  high:     "#ff6b35",
  medium:   "#ffd60a",
  low:      "#30d158",
};

const BORDER_COUNTRIES = ["pakistan","china","bangladesh","nepal","bhutan","myanmar","sri lanka","afghanistan"];
const CAT_COLORS = ["#6366f1","#8b5cf6","#ec4899","#f97316","#eab308","#22c55e","#14b8a6","#3b82f6"];

// ── Helpers ───────────────────────────────────────────────────────────────────

const DarkTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:"#0d1117", border:"1px solid #30363d", borderRadius:8, padding:"10px 14px" }}>
      <div style={{ color:"#8b949e", fontSize:11, marginBottom:4 }}>{label}</div>
      {payload.map((p,i) => (
        <div key={i} style={{ color:p.color||"#e6edf3", fontSize:13, fontWeight:700 }}>{p.name}: {p.value}</div>
      ))}
    </div>
  );
};

function SevBadge({ level }) {
  const c = SEV_COLOR[level?.toLowerCase()] || "#8b949e";
  return (
    <span style={{ background:c+"22", color:c, border:`1px solid ${c}44`, padding:"2px 8px", borderRadius:4, fontSize:10, fontWeight:800, letterSpacing:1, textTransform:"uppercase" }}>
      {level || "unknown"}
    </span>
  );
}

function Panel({ title, dot="#6366f1", children, style={} }) {
  return (
    <div style={{ background:"#0d1117", border:"1px solid #21262d", borderRadius:10, padding:"16px 18px", ...style }}>
      {title && (
        <div style={{ display:"flex", alignItems:"center", gap:8, fontFamily:"'IBM Plex Mono',monospace", fontSize:11, fontWeight:700, letterSpacing:1.5, color:"#6e7681", textTransform:"uppercase", marginBottom:14 }}>
          <span style={{ width:8, height:8, borderRadius:"50%", background:dot, flexShrink:0 }}/>
          {title}
        </div>
      )}
      {children}
    </div>
  );
}

function MetricCard({ icon, label, value, color, trend }) {
  return (
    <div style={{ flex:1, minWidth:150, background:"#0d1117", border:`1px solid ${color}44`, borderRadius:10, padding:"16px 18px", position:"relative", overflow:"hidden", transition:"transform 0.15s" }}
      onMouseEnter={e=>e.currentTarget.style.transform="translateY(-2px)"}
      onMouseLeave={e=>e.currentTarget.style.transform="translateY(0)"}>
      <div style={{ position:"absolute", top:0, right:0, width:80, height:80, background:color+"18", borderRadius:"0 10px 0 80px" }}/>
      <div style={{ fontSize:20, marginBottom:4 }}>{icon}</div>
      <div style={{ color:"#6e7681", fontSize:10, textTransform:"uppercase", letterSpacing:1, marginBottom:2 }}>{label}</div>
      <div style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:32, fontWeight:800, lineHeight:1, color }}>{value ?? 0}</div>
      {trend && <div style={{ color:"#484f58", fontSize:10, marginTop:4 }}>{trend}</div>}
    </div>
  );
}

// ── Filter Bar ────────────────────────────────────────────────────────────────

function FilterBar({ filters, setFilters, countries, states, incidentTypes }) {
  const sel = (key, val) => setFilters(f => ({ ...f, [key]: val }));

  const selectStyle = {
    background:"#161b22", border:"1px solid #30363d", color:"#e6edf3",
    borderRadius:6, padding:"6px 10px", fontSize:12,
    fontFamily:"'IBM Plex Mono',monospace", cursor:"pointer", outline:"none", minWidth:140
  };

  const hasFilter = filters.country || filters.state || filters.incident_type || filters.severity;

  return (
    <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center", background:"#0d1117", border:"1px solid #21262d", borderRadius:10, padding:"12px 16px", marginBottom:20 }}>
      <span style={{ color:"#484f58", fontSize:11, fontFamily:"'IBM Plex Mono',monospace", letterSpacing:1, textTransform:"uppercase", marginRight:4 }}>🔍 Filter</span>

      <select style={selectStyle} value={filters.country} onChange={e=>sel("country",e.target.value)}>
        <option value="">All Countries</option>
        {countries.map(c=><option key={c} value={c}>{c}</option>)}
      </select>

      <select style={selectStyle} value={filters.state} onChange={e=>sel("state",e.target.value)}>
        <option value="">All States</option>
        {states.map(s=><option key={s} value={s}>{s}</option>)}
      </select>

      <select style={selectStyle} value={filters.incident_type} onChange={e=>sel("incident_type",e.target.value)}>
        <option value="">Incident Type</option>
        {incidentTypes.map(t=>(
          <option key={t} value={t}>{t?.replace(/_/g," ")}</option>
        ))}
      </select>

      <select
        style={{ ...selectStyle, color: filters.severity ? SEV_COLOR[filters.severity] : "#e6edf3", borderColor: filters.severity ? SEV_COLOR[filters.severity]+"66" : "#30363d" }}
        value={filters.severity} onChange={e=>sel("severity",e.target.value)}>
        <option value="">All Severities</option>
        <option value="critical">🔴 CRITICAL</option>
        <option value="high">🟠 HIGH</option>
        <option value="medium">🟡 MEDIUM</option>
        <option value="low">🟢 LOW</option>
      </select>

      {filters.severity && (
        <div style={{ display:"flex", alignItems:"center", gap:6, background:SEV_COLOR[filters.severity]+"18", border:`1px solid ${SEV_COLOR[filters.severity]}44`, borderRadius:6, padding:"4px 10px" }}>
          <span style={{ width:8, height:8, borderRadius:"50%", background:SEV_COLOR[filters.severity] }}/>
          <span style={{ color:SEV_COLOR[filters.severity], fontSize:11, fontFamily:"'IBM Plex Mono',monospace", fontWeight:700 }}>
            Showing {filters.severity.toUpperCase()} only
          </span>
        </div>
      )}

      {hasFilter && (
        <button onClick={()=>setFilters({country:"",state:"",incident_type:"",severity:""})}
          style={{ background:"#ff2d5518", color:"#ff2d55", border:"1px solid #ff2d5544", borderRadius:6, padding:"6px 12px", fontSize:11, cursor:"pointer", fontFamily:"'IBM Plex Mono',monospace" }}>
          ✕ Clear All
        </button>
      )}
    </div>
  );
}

// ── Apply Filters ─────────────────────────────────────────────────────────────

function applyFilters(list, filters) {
  return list.filter(inc => {
    if (filters.country && !(inc.country||"").toLowerCase().includes(filters.country.toLowerCase())) return false;
    if (filters.state) {
      // Match state name against state field, content, summary, or url
      const s = filters.state.toLowerCase();
      const inState   = (inc.state||"").toLowerCase().includes(s);
      const inContent = (inc.content||"").toLowerCase().includes(s);
      const inSummary = (inc.summary||"").toLowerCase().includes(s);
      if (!inState && !inContent && !inSummary) return false;
    }
    if (filters.incident_type && (inc.incident_type||"").toLowerCase() !== filters.incident_type.toLowerCase()) return false;
    if (filters.severity      && (inc.severity||"").toLowerCase() !== filters.severity.toLowerCase())           return false;
    return true;
  });
}

// ── Risk Level Box ────────────────────────────────────────────────────────────

function RiskBox({ level, incidents, activeLevel, onClick }) {
  const color    = SEV_COLOR[level] || "#8b949e";
  const icons    = { critical:"🔴", high:"🟠", medium:"🟡", low:"🟢" };
  const filtered = incidents.filter(i => (i.severity||"").toLowerCase() === level)
                             .sort((a,b) => (b.risk_score||0)-(a.risk_score||0));
  const top      = filtered[0];
  const isActive = activeLevel === level;

  return (
    <div onClick={()=>onClick(level)}
      style={{ flex:1, minWidth:220, background:"#0d1117", border:`2px solid ${isActive ? color : color+"33"}`, borderRadius:10, overflow:"hidden", display:"flex", flexDirection:"column", cursor:"pointer", transition:"all 0.15s", transform: isActive?"translateY(-3px)":"translateY(0)" }}
      onMouseEnter={e=>{ if(!isActive){ e.currentTarget.style.borderColor=color+"88"; e.currentTarget.style.transform="translateY(-2px)"; }}}
      onMouseLeave={e=>{ if(!isActive){ e.currentTarget.style.borderColor=color+"33"; e.currentTarget.style.transform="translateY(0)"; }}}>
      <div style={{ background: isActive ? color+"30" : color+"18", borderBottom:`1px solid ${color}33`, padding:"10px 14px", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <span>{icons[level]}</span>
          <span style={{ color, fontFamily:"'IBM Plex Mono',monospace", fontSize:11, fontWeight:800, letterSpacing:2, textTransform:"uppercase" }}>{level}</span>
          {isActive && <span style={{ color:"#fff", background:color, fontSize:9, padding:"1px 6px", borderRadius:10, letterSpacing:1 }}>ACTIVE</span>}
        </div>
        <span style={{ background:color+"33", color, fontFamily:"'IBM Plex Mono',monospace", fontSize:12, fontWeight:800, padding:"2px 8px", borderRadius:20 }}>{filtered.length}</span>
      </div>
      <div style={{ padding:"12px 14px", flex:1 }}>
        {top ? (
          <>
            <div style={{ display:"flex", gap:6, marginBottom:8, flexWrap:"wrap", alignItems:"center" }}>
              <span style={{ color:"#6366f1", fontSize:11 }}>{top.incident_type?.replace(/_/g," ")||"—"}</span>
              {top.state   && <span style={{ color:"#484f58", fontSize:11 }}>· {top.state}</span>}
              {top.country && <span style={{ color:"#f97316", fontSize:11 }}>· {top.country}</span>}
              {top.risk_score != null && (
                <span style={{ color, fontSize:11, marginLeft:"auto", fontFamily:"monospace", fontWeight:700 }}>
                  Risk: {Math.round((top.risk_score||0)*100)}%
                </span>
              )}
            </div>
            <p style={{ color:"#c9d1d9", fontSize:12, margin:0, lineHeight:1.6, display:"-webkit-box", WebkitLineClamp:3, WebkitBoxOrient:"vertical", overflow:"hidden" }}>
              {top.summary || top.content?.slice(0,180) || "No summary available"}
            </p>
            <div style={{ color:"#484f58", fontSize:10, marginTop:8, fontFamily:"'IBM Plex Mono',monospace" }}>
              {top.source} · {top.collected_at ? new Date(top.collected_at).toLocaleDateString() : ""}
            </div>
          </>
        ) : (
          <div style={{ color:"#484f58", fontSize:12, textAlign:"center", padding:"20px 0" }}>No {level} incidents</div>
        )}
      </div>
      {filtered.length > 1 && (
        <div style={{ borderTop:`1px solid ${color}22`, padding:"8px 14px", background:color+"08" }}>
          <span style={{ color:color+"88", fontSize:11, fontFamily:"'IBM Plex Mono',monospace" }}>
            {isActive ? "Click to deselect":"Click to filter"} · +{filtered.length-1} more
          </span>
        </div>
      )}
    </div>
  );
}

// ── Border Countries Box ──────────────────────────────────────────────────────

function BorderNewsBox({ incidents }) {
  const borderInc = incidents
    .filter(i => BORDER_COUNTRIES.some(c => (i.country||"").toLowerCase().includes(c)))
    .sort((a,b) => (b.risk_score||0)-(a.risk_score||0));

  return (
    <Panel title="Border & Neighbouring Countries Intelligence" dot="#f97316" style={{ marginBottom:20 }}>
      {borderInc.length === 0 ? (
        <div style={{ color:"#484f58", fontSize:13, padding:"10px 0" }}>No border country incidents found in current dataset</div>
      ) : (
        <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
          {borderInc.slice(0,5).map((inc,i) => {
            const color   = SEV_COLOR[inc.severity?.toLowerCase()]||"#8b949e";
            const riskPct = inc.risk_score != null ? Math.round((inc.risk_score||0)*100) : null;
            return (
              <div key={i} style={{ display:"flex", gap:12, padding:"12px 14px", background:"#161b22", borderRadius:8, borderLeft:`3px solid ${color}` }}>
                <div style={{ flex:1 }}>
                  <div style={{ display:"flex", gap:8, alignItems:"center", marginBottom:6, flexWrap:"wrap" }}>
                    <SevBadge level={inc.severity}/>
                    <span style={{ color:"#f97316", fontSize:12, fontWeight:700 }}>🌏 {inc.country}</span>
                    <span style={{ color:"#6366f1", fontSize:11 }}>{inc.incident_type?.replace(/_/g," ")}</span>
                    {riskPct != null && (
                      <span style={{ color, fontSize:11, fontFamily:"monospace", fontWeight:700, marginLeft:"auto", background:color+"18", padding:"2px 8px", borderRadius:4 }}>
                        Risk {riskPct}%
                      </span>
                    )}
                  </div>
                  <p style={{ color:"#c9d1d9", fontSize:12, margin:0, lineHeight:1.6 }}>
                    {inc.summary || inc.content?.slice(0,200) || "No summary available"}
                  </p>
                  <div style={{ color:"#484f58", fontSize:10, marginTop:6, fontFamily:"'IBM Plex Mono',monospace" }}>
                    {inc.source} · {inc.collected_at ? new Date(inc.collected_at).toLocaleDateString() : ""}
                  </div>
                </div>
              </div>
            );
          })}
          {borderInc.length > 5 && (
            <div style={{ color:"#484f58", fontSize:12, textAlign:"center", padding:"6px 0" }}>+{borderInc.length-5} more border incidents</div>
          )}
        </div>
      )}
    </Panel>
  );
}

// ── Report Card ───────────────────────────────────────────────────────────────

function ReportCard({ inc }) {
  const [expanded, setExpanded] = useState(false);
  const color   = SEV_COLOR[inc.severity?.toLowerCase()]||"#6366f1";
  const riskPct = inc.risk_score != null ? Math.round((inc.risk_score||0)*100) : null;
  const text    = inc.summary || inc.content || "No content available";

  return (
    <div style={{ background:"#0d1117", border:"1px solid #21262d", borderRadius:12, overflow:"hidden", transition:"transform 0.15s, border-color 0.15s" }}
      onMouseEnter={e=>{ e.currentTarget.style.transform="translateY(-2px)"; e.currentTarget.style.borderColor=color+"55"; }}
      onMouseLeave={e=>{ e.currentTarget.style.transform="translateY(0)";    e.currentTarget.style.borderColor="#21262d"; }}>
      <div style={{ height:3, background:`linear-gradient(90deg,${color},${color}44)` }}/>
      <div style={{ padding:"16px 18px" }}>
        <div style={{ display:"flex", gap:8, alignItems:"center", marginBottom:10, flexWrap:"wrap" }}>
          <SevBadge level={inc.severity}/>
          <span style={{ color:"#6366f1", fontSize:11 }}>{inc.incident_type?.replace(/_/g," ")||"unclassified"}</span>
          {inc.country && <span style={{ color:"#f97316", fontSize:11 }}>🌏 {inc.country}</span>}
          {inc.state   && <span style={{ color:"#484f58", fontSize:11 }}>📍 {inc.state}</span>}
          {riskPct != null && (
            <span style={{ color, fontSize:11, fontFamily:"monospace", fontWeight:800, marginLeft:"auto", background:color+"18", padding:"2px 8px", borderRadius:4 }}>
              Risk {riskPct}%
            </span>
          )}
        </div>
        <p style={{ color:"#c9d1d9", fontSize:13, margin:"0 0 10px", lineHeight:1.7, display:expanded?"block":"-webkit-box", WebkitLineClamp:expanded?undefined:3, WebkitBoxOrient:"vertical", overflow:expanded?"visible":"hidden" }}>
          {text}
        </p>
        {text.length > 200 && (
          <button onClick={()=>setExpanded(e=>!e)} style={{ background:"none", border:"none", color:"#6366f1", fontSize:12, cursor:"pointer", padding:0, fontFamily:"'IBM Plex Mono',monospace" }}>
            {expanded?"▲ Show less":"▼ Read more"}
          </button>
        )}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:12, paddingTop:10, borderTop:"1px solid #21262d" }}>
          <span style={{ color:"#484f58", fontSize:11, fontFamily:"'IBM Plex Mono',monospace" }}>{inc.source}</span>
          <div style={{ display:"flex", gap:10, alignItems:"center" }}>
            <span style={{ color:"#484f58", fontSize:11 }}>{inc.collected_at ? new Date(inc.collected_at).toLocaleString() : ""}</span>
            {inc.url && <a href={inc.url} target="_blank" rel="noreferrer" style={{ color:"#6366f1", fontSize:11, textDecoration:"none" }}>Source →</a>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Risk Score Table ──────────────────────────────────────────────────────────

function RiskScoreTable({ riskScores }) {
  return (
    <Panel title="Risk Scores by State" dot="#ff6b35">
      <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}>
        <thead>
          <tr>
            {["State","Avg Risk","Max Risk","Incidents"].map(h=>(
              <th key={h} style={{ padding:"8px 10px", color:"#484f58", fontSize:10, textAlign:"left", letterSpacing:1, textTransform:"uppercase", borderBottom:"1px solid #21262d", fontFamily:"'IBM Plex Mono',monospace" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {riskScores?.slice(0,10).map((r,i)=>{
            const pct = Math.round((r.avg_risk||0)*100);
            const c   = pct>=75?"#ff2d55":pct>=50?"#ff6b35":pct>=25?"#ffd60a":"#30d158";
            return (
              <tr key={i} style={{ background:i%2===0?"#0d111750":"transparent" }}>
                <td style={{ padding:"8px 10px", color:"#e6edf3" }}>{r.state}</td>
                <td style={{ padding:"8px 10px" }}>
                  <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                    <div style={{ width:60, height:6, background:"#21262d", borderRadius:3, overflow:"hidden" }}>
                      <div style={{ width:`${pct}%`, height:"100%", background:c, borderRadius:3 }}/>
                    </div>
                    <span style={{ color:c, fontWeight:800, fontFamily:"monospace" }}>{pct}%</span>
                  </div>
                </td>
                <td style={{ padding:"8px 10px", color:"#ff2d55", fontFamily:"monospace", fontWeight:700 }}>{Math.round((r.max_risk||0)*100)}%</td>
                <td style={{ padding:"8px 10px", color:"#8b949e" }}>{r.total_incidents}</td>
              </tr>
            );
          })}
          {!riskScores?.length && <tr><td colSpan={4} style={{ color:"#484f58", textAlign:"center", padding:24 }}>No data yet</td></tr>}
        </tbody>
      </table>
    </Panel>
  );
}

// ── Alerts List ───────────────────────────────────────────────────────────────

function AlertsList({ alerts }) {
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
      {alerts?.slice(0,6).map((a,i)=>(
        <div key={i} style={{ display:"flex", alignItems:"flex-start", gap:10, padding:"10px 12px", background:"#161b22", borderLeft:`3px solid ${SEV_COLOR[a.alert_type?.toLowerCase()]||"#30363d"}`, borderRadius:"0 6px 6px 0" }}>
          <span style={{ width:8, height:8, borderRadius:"50%", background:SEV_COLOR[a.alert_type?.toLowerCase()]||"#8b949e", marginTop:3, flexShrink:0 }}/>
          <div>
            <span style={{ color:SEV_COLOR[a.alert_type?.toLowerCase()]||"#8b949e", fontSize:10, fontWeight:800, letterSpacing:1, marginRight:8 }}>{a.alert_type?.toUpperCase()}</span>
            <span style={{ color:"#8b949e", fontSize:13 }}>{a.keyword} — {a.state||a.country||"—"}</span>
            {a.threat_probability && <span style={{ color:"#ffd60a", fontSize:11, marginLeft:8 }}>threat: {Math.round(a.threat_probability*100)}%</span>}
          </div>
        </div>
      ))}
      {!alerts?.length && <div style={{ color:"#484f58", fontSize:13, padding:"10px 0" }}>No active alerts</div>}
    </div>
  );
}

// ── Operations Panel ──────────────────────────────────────────────────────────

function OperationsPanel({ schedulerStatus, onRefreshStatus }) {
  const [log, setLog]         = useState([{ msg:"$ system ready", type:"info", time:new Date().toLocaleTimeString() }]);
  const [running, setRunning] = useState({});
  const [dbStats, setDbStats] = useState(null);

  const addLog = (msg, type="info") => setLog(p=>[...p.slice(-29),{ msg, type, time:new Date().toLocaleTimeString() }]);

  const run = async (label, url, method="post") => {
    setRunning(r=>({...r,[label]:true}));
    addLog(`Starting ${label}...`);
    try {
      const res = method==="post" ? await axios.post(url) : await axios.get(url);
      addLog(`✓ ${label} completed`, "success");
      if (label==="DB Stats") setDbStats(res.data);
      if (["Start Scheduler","Stop Scheduler","Scheduler Status"].includes(label)) onRefreshStatus();
      return res.data;
    } catch(e) {
      addLog(`✗ ${label} failed — ${e?.response?.status||"check backend"}`, "error");
    } finally {
      setRunning(r=>({...r,[label]:false}));
    }
  };

  const isActive = schedulerStatus?.running;

  const btnStyle = (color, disabled) => ({
    padding:"10px 16px", borderRadius:8, cursor:disabled?"not-allowed":"pointer",
    background:disabled?"#21262d":color+"18", color:disabled?"#6e7681":color,
    border:`1px solid ${disabled?"#30363d":color+"44"}`,
    fontFamily:"'IBM Plex Mono',monospace", fontSize:12, fontWeight:700, textAlign:"left"
  });

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
      <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>

        {/* Ingestion & AI */}
        <Panel title="Ingestion & AI" dot="#0a84ff" style={{ flex:1, minWidth:240 }}>
          <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
            <button onClick={()=>run("Run Ingestion",`${OPS}/run-ingestion`)} disabled={running["Run Ingestion"]}
              style={btnStyle("#0a84ff", running["Run Ingestion"])}>
              {running["Run Ingestion"]?"⟳ Running...":"▶ Run Ingestion"}
            </button>
            <button onClick={()=>run("Run AI Analysis",`${OPS}/run-ai`)} disabled={running["Run AI Analysis"]}
              style={btnStyle("#6366f1", running["Run AI Analysis"])}>
              {running["Run AI Analysis"]?"⟳ Processing...":"⚡ Run AI Analysis"}
            </button>
          </div>
        </Panel>

        {/* Scheduler */}
        <Panel title="Scheduler" dot="#30d158" style={{ flex:1, minWidth:240 }}>
          <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
            <div style={{ display:"flex", alignItems:"center", gap:10, padding:"10px 14px", background:"#161b22", borderRadius:8, border:"1px solid #21262d" }}>
              <span style={{ width:10, height:10, borderRadius:"50%", background:isActive?"#30d158":"#ff2d55", boxShadow:isActive?"0 0 8px #30d158":"none", flexShrink:0 }}/>
              <span style={{ color:isActive?"#30d158":"#ff2d55", fontWeight:700, fontSize:13, fontFamily:"'IBM Plex Mono',monospace" }}>
                {isActive?"ACTIVE":"INACTIVE"}
              </span>
              <button onClick={()=>run("Scheduler Status",`${OPS}/scheduler-status`,"get")}
                style={{ marginLeft:"auto", background:"#21262d", border:"1px solid #30363d", borderRadius:6, color:"#8b949e", fontSize:11, padding:"4px 8px", cursor:"pointer", fontFamily:"'IBM Plex Mono',monospace" }}>
                ↺
              </button>
            </div>
            <div style={{ display:"flex", gap:8 }}>
              <button onClick={()=>run("Start Scheduler",`${OPS}/start-scheduler`)} disabled={running["Start Scheduler"]||isActive}
                style={{ ...btnStyle("#30d158", running["Start Scheduler"]||isActive), flex:1 }}>
                ▶ Start
              </button>
              <button onClick={()=>run("Stop Scheduler",`${OPS}/stop-scheduler`)} disabled={running["Stop Scheduler"]||!isActive}
                style={{ ...btnStyle("#ff2d55", running["Stop Scheduler"]||!isActive), flex:1 }}>
                ■ Stop
              </button>
            </div>
          </div>
        </Panel>

        {/* DB Stats */}
        <Panel title="Database Stats" dot="#ffd60a" style={{ flex:1, minWidth:240 }}>
          {dbStats ? (
            <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
              {Object.entries(dbStats).map(([k,v])=>(
                <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"6px 10px", background:"#161b22", borderRadius:6 }}>
                  <span style={{ color:"#8b949e", fontSize:12, fontFamily:"'IBM Plex Mono',monospace" }}>{k.replace(/_/g," ")}</span>
                  <span style={{ color:"#ffd60a", fontWeight:700, fontFamily:"monospace" }}>{String(v)}</span>
                </div>
              ))}
              <button onClick={()=>setDbStats(null)} style={{ background:"none", border:"none", color:"#484f58", fontSize:11, cursor:"pointer", padding:"4px 0", fontFamily:"'IBM Plex Mono',monospace" }}>↺ Reload</button>
            </div>
          ) : (
            <button onClick={()=>run("DB Stats",`${OPS}/db-stats`,"get")} disabled={running["DB Stats"]}
              style={btnStyle("#ffd60a", running["DB Stats"])}>
              {running["DB Stats"]?"⟳ Loading...":"📊 Load DB Stats"}
            </button>
          )}
        </Panel>
      </div>

      {/* System Log */}
      <Panel title="System Log" dot="#ffd60a">
        <div style={{ background:"#161b22", borderRadius:8, padding:12, fontFamily:"monospace", fontSize:12, height:220, overflowY:"auto", border:"1px solid #21262d" }}>
          {log.map((l,i)=>(
            <div key={i} style={{ color:l.type==="success"?"#30d158":l.type==="error"?"#ff2d55":"#8b949e", marginBottom:4 }}>
              <span style={{ color:"#484f58" }}>[{l.time}]</span> {l.msg}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

export default function OSNITDashboard() {
  const [tab, setTab]               = useState("Overview");
  const [summary, setSummary]       = useState(null);
  const [trends, setTrends]         = useState([]);
  const [alerts, setAlerts]         = useState([]);
  const [riskScores, setRiskScores] = useState([]);
  const [allIncidents, setAllIncidents] = useState([]);  // from /incidents/
  const [countries, setCountries]   = useState([]);
  const [states, setStates]         = useState([]);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [loading, setLoading]       = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [filters, setFilters]       = useState({ country:"", state:"", incident_type:"", severity:"" });

  const fetchSchedulerStatus = useCallback(async () => {
    try { const r = await axios.get(`${OPS}/scheduler-status`); setSchedulerStatus(r.data); } catch {}
  }, []);

  const fetchAll = useCallback(async () => {
    const r = await Promise.allSettled([
      axios.get(`${INTEL}/summary`),           // 0
      axios.get(`${INTEL}/trend`),             // 1
      axios.get(`${INTEL}/alerts`),            // 2
      axios.get(`${INTEL}/risk-scores`),       // 3
      axios.get(`${INC}/?limit=200`),          // 4 — all incidents with content
      axios.get(`${OPS}/scheduler-status`),    // 5
    ]);
    const d = i => r[i].status==="fulfilled" ? r[i].value.data : null;

    if (d(0)) setSummary(d(0));
    if (d(1)) setTrends(d(1)||[]);
    if (d(2)) setAlerts(d(2)||[]);
    if (d(3)) setRiskScores(d(3)||[]);
    if (d(5)) setSchedulerStatus(d(5));

    // Load incidents from /incidents/ endpoint
    if (d(4)) {
      const incs = Array.isArray(d(4)) ? d(4) : d(4)?.incidents || d(4)?.data || [];
      setAllIncidents(incs);

      // Extract countries and states from real incident data — clean strings only
      const rawCountries = [...new Set(incs.map(i=>i.country).filter(v=>v && typeof v==="string" && !v.includes(",") && v.length<50))].sort();
      setCountries(rawCountries);
    }

    // States — hardcoded India states (DB stores coordinates not names)
    setStates([
      "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
      "Goa","Gujarat","Haryana","Himachal Pradesh","Jammu & Kashmir",
      "Jharkhand","Karnataka","Kerala","Ladakh","Madhya Pradesh",
      "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
      "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu",
      "Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
      "Delhi","Chandigarh","Puducherry","Lakshadweep","Andaman & Nicobar Islands"
    ]);

    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 30000);
    return () => clearInterval(id);
  }, [fetchAll]);

  // Filtered incidents
  const filtered = applyFilters(allIncidents, filters);
  const displayList = filtered;

  // Incident types from real data
  const incidentTypes = [...new Set(allIncidents.map(i=>i.incident_type).filter(Boolean))].sort();

  const trendData = trends.map(t=>({ date:t.date||"", count:t.count||0 }));
  const catData   = (summary?.top_incident_types||[]).map((t,i)=>({
    name:  t.type?.replace(/_/g," ")||"other",
    count: t.count,
    fill:  CAT_COLORS[i%CAT_COLORS.length]
  }));

  const SLabel = ({ children }) => (
    <div style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:11, fontWeight:700, letterSpacing:2, color:"#6e7681", textTransform:"uppercase", margin:"20px 0 10px" }}>{children}</div>
  );

  const handleRiskBoxClick = (level) => {
    setFilters(f => ({ ...f, severity: f.severity===level ? "" : level }));
  };

  if (loading) return (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#010409", flexDirection:"column", gap:16 }}>
      <div style={{ width:36, height:36, border:"3px solid #21262d", borderTopColor:"#6366f1", borderRadius:"50%", animation:"spin 0.8s linear infinite" }}/>
      <div style={{ color:"#6e7681", fontFamily:"'IBM Plex Mono',monospace", letterSpacing:2, fontSize:12 }}>LOADING OSNIT SHIELD...</div>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );

  return (
    <div style={{ minHeight:"100vh", background:"#010409", color:"#e6edf3", fontFamily:"'IBM Plex Sans',sans-serif", fontSize:14 }}>

      {/* Header */}
      <header style={{ display:"flex", alignItems:"center", gap:12, padding:"0 24px", height:56, background:"#0d1117", borderBottom:"1px solid #21262d", position:"sticky", top:0, zIndex:200, flexWrap:"wrap" }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ fontSize:22 }}>🛡</span>
          <span style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:16, letterSpacing:1 }}>
            OSNIT <strong style={{ color:"#6366f1" }}>Shield</strong>
          </span>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:6, background:"#161b22", border:"1px solid #21262d", borderRadius:6, padding:"4px 10px" }}>
          <span style={{ width:7, height:7, borderRadius:"50%", background:schedulerStatus?.running?"#30d158":"#ff2d55", boxShadow:schedulerStatus?.running?"0 0 6px #30d158":"none" }}/>
          <span style={{ color:"#8b949e", fontSize:11, fontFamily:"'IBM Plex Mono',monospace" }}>
            Scheduler: <strong style={{ color:schedulerStatus?.running?"#30d158":"#ff2d55" }}>{schedulerStatus?.running?"ON":"OFF"}</strong>
          </span>
        </div>
        {/* Refresh button */}
        <button
          onClick={() => { setLoading(false); fetchAll(); }}
          style={{ padding:"6px 16px", borderRadius:6, cursor:"pointer", background:"#6366f118", color:"#6366f1", border:"1px solid #6366f144", fontFamily:"'IBM Plex Mono',monospace", fontSize:11, fontWeight:700, display:"flex", alignItems:"center", gap:6 }}>
          ↺ Refresh
        </button>
        <div style={{ color:"#484f58", fontSize:12, marginLeft:"auto" }}>
          {allIncidents.length} incidents loaded · Last: {lastUpdate ? lastUpdate.toLocaleTimeString() : "—"}
        </div>
      </header>

      {/* Nav */}
      <nav style={{ display:"flex", background:"#0d1117", borderBottom:"1px solid #21262d", padding:"0 24px" }}>
        {TABS.map(t=>(
          <button key={t} onClick={()=>setTab(t)} style={{ background:"transparent", border:"none", borderBottom:tab===t?"2px solid #6366f1":"2px solid transparent", color:tab===t?"#e6edf3":"#6e7681", padding:"12px 18px", cursor:"pointer", fontFamily:"'IBM Plex Sans',sans-serif", fontSize:13, fontWeight:tab===t?700:400, transition:"all 0.15s" }}>{t}</button>
        ))}
      </nav>

      <div style={{ padding:24, maxWidth:1600, margin:"0 auto" }}>

        {/* ── Overview ── */}
        {tab==="Overview" && (
          <>
            <div style={{ display:"flex", gap:14, marginBottom:20, flexWrap:"wrap" }}>
              <MetricCard icon="🔥" label="High Severity"  value={summary?.severity_breakdown?.high??0}   color="#ff2d55" trend={`Critical: ${summary?.severity_breakdown?.critical??0}`}/>
              <MetricCard icon="⚠️" label="Active Alerts"  value={summary?.total_alerts??0}               color="#ffd60a" trend="all time"/>
              <MetricCard icon="📈" label="Avg Risk Score" value={summary?.average_risk_score ? `${Math.round(summary.average_risk_score*100)}%`:"0%"} color="#30d158" trend="across all incidents"/>
              <MetricCard icon="🗄️" label="Last 24h"       value={summary?.incidents_last_24h??0}          color="#0a84ff" trend={`Total: ${summary?.total_incidents??0}`}/>
            </div>

            <FilterBar filters={filters} setFilters={setFilters} countries={countries} states={states} incidentTypes={incidentTypes}/>

            {/* Risk level boxes */}
            <div style={{ marginBottom:20 }}>
              <div style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:11, fontWeight:700, letterSpacing:2, color:"#6e7681", textTransform:"uppercase", marginBottom:12, display:"flex", alignItems:"center", gap:8 }}>
                <span style={{ width:8, height:8, borderRadius:"50%", background:"#6366f1" }}/>
                Incidents by Risk Level
                <span style={{ color:"#484f58", fontSize:10, fontWeight:400, letterSpacing:0.5, marginLeft:4 }}>— click a box to filter</span>
              </div>
              <div style={{ display:"flex", gap:14, flexWrap:"wrap" }}>
                {["critical","high","medium","low"].map(level=>(
                  <RiskBox key={level} level={level} incidents={allIncidents} activeLevel={filters.severity} onClick={handleRiskBoxClick}/>
                ))}
              </div>
            </div>

            {/* Show filtered results when severity selected */}
            {filters.severity && (
              <Panel title={`${filters.severity.toUpperCase()} Risk Incidents (${displayList.length})`} dot={SEV_COLOR[filters.severity]} style={{ marginBottom:20 }}>
                {displayList.length===0 ? (
                  <div style={{ color:"#484f58", fontSize:13, padding:"10px 0" }}>No {filters.severity} incidents match current filters</div>
                ) : (
                  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                    {displayList.slice(0,20).map((inc,i)=>(
                      <div key={inc.id||i} style={{ padding:"12px 14px", background:"#161b22", borderRadius:8, borderLeft:`3px solid ${SEV_COLOR[inc.severity?.toLowerCase()]||"#30363d"}` }}>
                        <div style={{ display:"flex", gap:8, alignItems:"center", marginBottom:6, flexWrap:"wrap" }}>
                          <span style={{ color:"#6366f1", fontSize:11 }}>{inc.incident_type?.replace(/_/g," ")||"—"}</span>
                          {inc.state   && <span style={{ color:"#484f58", fontSize:11 }}>📍 {inc.state}</span>}
                          {inc.country && <span style={{ color:"#f97316", fontSize:11 }}>🌏 {inc.country}</span>}
                          {inc.risk_score != null && <span style={{ color:SEV_COLOR[inc.severity?.toLowerCase()]||"#8b949e", fontSize:11, fontFamily:"monospace", fontWeight:700, marginLeft:"auto" }}>Risk {Math.round((inc.risk_score||0)*100)}%</span>}
                        </div>
                        <p style={{ color:"#c9d1d9", fontSize:12, margin:0, lineHeight:1.6 }}>{inc.summary || inc.content?.slice(0,200) || "No summary"}</p>
                        <div style={{ color:"#484f58", fontSize:10, marginTop:6, fontFamily:"'IBM Plex Mono',monospace" }}>{inc.source} · {inc.collected_at ? new Date(inc.collected_at).toLocaleDateString():""}</div>
                      </div>
                    ))}
                    {displayList.length > 20 && <div style={{ color:"#484f58", fontSize:12, textAlign:"center", padding:"8px 0" }}>+{displayList.length-20} more — go to Explorer tab</div>}
                  </div>
                )}
              </Panel>
            )}

            <BorderNewsBox incidents={allIncidents}/>
            <Panel title="Recent Alerts" dot="#ffd60a">
              <AlertsList alerts={alerts}/>
            </Panel>
          </>
        )}

        {/* ── Intelligence ── */}
        {tab==="Intelligence" && (
          <>
            <FilterBar filters={filters} setFilters={setFilters} countries={countries} states={states} incidentTypes={incidentTypes}/>
            <div style={{ display:"flex", gap:16, flexWrap:"wrap", marginBottom:18 }}>
              <div style={{ flex:1, minWidth:300 }}><RiskScoreTable riskScores={riskScores}/></div>
              <Panel title="Incident Categories" dot="#6366f1" style={{ flex:1, minWidth:300 }}>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={catData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#21262d" horizontal={false}/>
                    <XAxis type="number" tick={{ fill:"#484f58", fontSize:10 }}/>
                    <YAxis type="category" dataKey="name" tick={{ fill:"#8b949e", fontSize:11 }} width={120}/>
                    <Tooltip content={<DarkTooltip/>}/>
                    <Bar dataKey="count" name="Count" radius={[0,5,5,0]} fill="#6366f1"/>
                  </BarChart>
                </ResponsiveContainer>
              </Panel>
            </div>
            <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
              <Panel title="7-Day Trend" dot="#30d158" style={{ flex:2, minWidth:300 }}>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={trendData}>
                    <defs>
                      <linearGradient id="gT" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#30d158" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#30d158" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#21262d"/>
                    <XAxis dataKey="date" tick={{ fill:"#484f58", fontSize:10 }}/>
                    <YAxis tick={{ fill:"#484f58", fontSize:10 }}/>
                    <Tooltip content={<DarkTooltip/>}/>
                    <Area type="monotone" dataKey="count" stroke="#30d158" fill="url(#gT)" strokeWidth={2} name="Incidents"/>
                  </AreaChart>
                </ResponsiveContainer>
              </Panel>
              <Panel title="Active Alerts" dot="#ffd60a" style={{ flex:1, minWidth:280 }}>
                <AlertsList alerts={alerts}/>
              </Panel>
            </div>
          </>
        )}

        {/* ── Reports ── */}
        {tab==="Reports" && (
          <>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16, flexWrap:"wrap", gap:10 }}>
              <div style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:13, fontWeight:700, letterSpacing:2, color:"#e6edf3", textTransform:"uppercase" }}>
                📋 Intelligence Reports
              </div>
              <span style={{ color:"#484f58", fontSize:12 }}>
                {displayList.length} of {allIncidents.length} reports
                {filters.severity && <span style={{ color:SEV_COLOR[filters.severity], marginLeft:8 }}>· {filters.severity.toUpperCase()} filter active</span>}
              </span>
            </div>
            <FilterBar filters={filters} setFilters={setFilters} countries={countries} states={states} incidentTypes={incidentTypes}/>
            {displayList.length === 0 ? (
              <div style={{ color:"#484f58", textAlign:"center", padding:60, fontSize:14 }}>
                {Object.values(filters).some(Boolean)
                  ? "No reports match the selected filters — try clearing some filters"
                  : "No incidents in database yet"}
              </div>
            ) : (
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(360px,1fr))", gap:16 }}>
                {displayList.map((inc,i)=><ReportCard key={inc.id||i} inc={inc}/>)}
              </div>
            )}
          </>
        )}

        {/* ── Explorer ── */}
        {tab==="Explorer" && (
          <>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
              <SLabel>Incident Explorer</SLabel>
              <span style={{ color:"#484f58", fontSize:12 }}>{displayList.length} of {allIncidents.length} records</span>
            </div>
            <FilterBar filters={filters} setFilters={setFilters} countries={countries} states={states} incidentTypes={incidentTypes}/>
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              {displayList.length>0 ? displayList.map((inc,i)=>(
                <div key={inc.id||i} style={{ background:"#0d1117", border:"1px solid #21262d", borderLeft:`4px solid ${SEV_COLOR[inc.severity?.toLowerCase()]||"#30363d"}`, borderRadius:"0 8px 8px 0", padding:"14px 16px" }}>
                  <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:8, flexWrap:"wrap" }}>
                    <SevBadge level={inc.severity}/>
                    <span style={{ color:"#6366f1", fontSize:12 }}>{inc.incident_type?.replace(/_/g," ")||"unclassified"}</span>
                    <span style={{ color:"#484f58", fontSize:11 }}>{inc.source}</span>
                    {inc.state   && <span style={{ color:"#30d15888", fontSize:11 }}>📍 {inc.state}</span>}
                    {inc.country && <span style={{ color:"#f9731688", fontSize:11 }}>🌏 {inc.country}</span>}
                    <span style={{ color:"#30363d", fontSize:11, marginLeft:"auto" }}>{inc.collected_at ? new Date(inc.collected_at).toLocaleString():""}</span>
                  </div>
                  {inc.summary && <p style={{ color:"#c9d1d9", fontSize:13, margin:"0 0 6px", lineHeight:1.6, background:"#161b22", padding:"8px 12px", borderRadius:6, borderLeft:"2px solid #6366f1" }}>{inc.summary}</p>}
                  {inc.url && <a href={inc.url} target="_blank" rel="noreferrer" style={{ color:"#6366f1", fontSize:12, textDecoration:"none" }}>Source →</a>}
                </div>
              )) : (
                <div style={{ color:"#484f58", textAlign:"center", padding:40 }}>
                  {Object.values(filters).some(Boolean) ? "No incidents match selected filters" : "No incidents in database"}
                </div>
              )}
            </div>
          </>
        )}

        {/* ── Operations ── */}
        {tab==="Operations" && (
          <>
            <SLabel>System Controls</SLabel>
            <OperationsPanel schedulerStatus={schedulerStatus} onRefreshStatus={fetchSchedulerStatus}/>
            <SLabel>System Summary</SLabel>
            <div style={{ display:"flex", gap:14, flexWrap:"wrap" }}>
              <MetricCard icon="📊" label="Total Incidents" value={summary?.total_incidents??0}   color="#6366f1"/>
              <MetricCard icon="🔔" label="Total Alerts"    value={summary?.total_alerts??0}       color="#ffd60a"/>
              <MetricCard icon="🎯" label="Avg Risk"        value={summary?.average_risk_score?`${Math.round(summary.average_risk_score*100)}%`:"0%"} color="#30d158"/>
              <MetricCard icon="📅" label="Last 24h"        value={summary?.incidents_last_24h??0} color="#0a84ff"/>
            </div>
          </>
        )}

      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;700&display=swap');
        *{box-sizing:border-box} body{margin:0}
        @keyframes spin{to{transform:rotate(360deg)}}
        ::-webkit-scrollbar{width:5px;height:5px}
        ::-webkit-scrollbar-track{background:#0d1117}
        ::-webkit-scrollbar-thumb{background:#21262d;border-radius:3px}
      `}</style>
    </div>
  );
}
