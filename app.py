"""
app.py — Streamlit host for a fully custom HTML/JS chat UI.
The UI is rendered via st.components.v1.html() and talks directly
to the FastAPI backend via fetch(). Streamlit is purely the deployment shell.
"""

import streamlit as st
import threading
import time
import logging
import sys
import os

st.set_page_config(
    page_title="Titanic Chat",
    page_icon="🚢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config import BACKEND_URL, BACKEND_PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Start FastAPI once per process ───────────────────────────────────────────
def _port_is_bound(port: int) -> bool:
    """Returns True if something is already listening on the given port."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0

def _start_backend() -> None:
    try:
        import uvicorn
        from backend.main import app as fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=BACKEND_PORT, log_level="warning")
    except Exception as e:
        logger.error(f"Backend thread error: {e}")

def _ensure_backend_running() -> None:
    """
    Only start the backend if nothing is already listening on BACKEND_PORT.
    Safely handles Streamlit Cloud re-running app.py on each session
    without causing address-already-in-use errors.
    """
    if not _port_is_bound(BACKEND_PORT):
        t = threading.Thread(target=_start_backend, daemon=True)
        t.start()
        logger.info(f"Backend thread started on port {BACKEND_PORT}")
        time.sleep(2)
    else:
        logger.info(f"Backend already running on port {BACKEND_PORT} — skipping start")

_ensure_backend_running()

# ── Strip all Streamlit chrome so only the iframe shows ─────────────────────
st.markdown("""
<style>
  #MainMenu, footer, header, .stDeployButton { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: #040d1a; }
  iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Build the HTML — f-string injects the backend URL at render time ─────────
CHAT_UI = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
  :root {{
    --deep:        #040d1a;
    --ocean:       #0a2040;
    --wave:        #0d3060;
    --foam:        #1a5080;
    --gold:        #c8a84b;
    --gold-light:  #e8c86b;
    --copper:      #b87333;
    --ice:         #a8d8f0;
    --mist:        #7aaec8;
    --text:        #d8e8f4;
    --text-dim:    #6a90b0;
    --danger:      #c0504a;
    --radius:      18px;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  html, body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--deep);
    color: var(--text);
    height: 100vh;
    overflow: hidden;
  }}

  /* Ocean background layers */
  body::before {{
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background:
      radial-gradient(ellipse 80% 60% at 15% 85%, rgba(10,50,110,0.55) 0%, transparent 60%),
      radial-gradient(ellipse 60% 70% at 85% 15%, rgba(5,25,70,0.7) 0%, transparent 55%),
      radial-gradient(ellipse 50% 50% at 50% 50%, rgba(10,30,70,0.3) 0%, transparent 70%),
      linear-gradient(180deg, #040d1a 0%, #071526 45%, #0a2040 100%);
    pointer-events: none;
  }}

  /* Subtle horizontal scan lines for depth */
  body::after {{
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background-image: repeating-linear-gradient(
      0deg,
      transparent, transparent 58px,
      rgba(13,48,96,0.08) 58px, rgba(13,48,96,0.08) 59px
    );
    pointer-events: none;
  }}

  /* Floating particles */
  .p {{ position:fixed; border-radius:50%; background:rgba(168,216,240,0.18); animation:drift linear infinite; z-index:0; pointer-events:none; }}
  @keyframes drift {{
    0%   {{ transform:translateY(105vh); opacity:0; }}
    8%   {{ opacity:0.8; }}
    92%  {{ opacity:0.4; }}
    100% {{ transform:translateY(-8vh) translateX(20px); opacity:0; }}
  }}

  /* ── App shell ── */
  .shell {{
    position: relative; z-index: 1;
    display: flex; flex-direction: column;
    height: 100vh;
    max-width: 760px;
    margin: 0 auto;
    padding: 0 18px;
  }}

  /* ── Header ── */
  .hdr {{
    padding: 18px 0 14px;
    display: flex; align-items: center; gap: 14px;
    border-bottom: 1px solid rgba(200,168,75,0.18);
    flex-shrink: 0;
  }}
  .hdr-icon {{
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--wave), var(--foam));
    border-radius: 50%;
    border: 2px solid rgba(200,168,75,0.7);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 22px rgba(200,168,75,0.25), inset 0 1px 0 rgba(255,255,255,0.1);
    flex-shrink: 0;
  }}
  .hdr-copy h1 {{
    font-family: 'Playfair Display', serif;
    font-size: 1.18rem; font-weight: 700;
    color: var(--gold-light);
    letter-spacing: 0.02em;
  }}
  .hdr-copy p {{
    font-size: 0.68rem; color: var(--text-dim);
    letter-spacing: 0.1em; text-transform: uppercase; margin-top: 2px;
  }}
  .hdr-status {{
    margin-left: auto; display:flex; align-items:center; gap:6px;
    font-size: 0.68rem; color: var(--text-dim); letter-spacing: 0.06em;
    flex-shrink: 0;
  }}
  .dot {{
    width:7px; height:7px; border-radius:50%;
    background:#4caf50; box-shadow: 0 0 7px #4caf50;
    animation: pdot 2.2s ease-in-out infinite;
  }}
  .dot.off {{ background:var(--danger); box-shadow:0 0 7px var(--danger); animation:none; }}
  @keyframes pdot {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:0.5;transform:scale(0.8)}} }}

  /* ── Suggestion chips ── */
  #chips-wrap {{
    padding: 16px 0 6px;
    flex-shrink: 0;
  }}
  .chips-label {{
    font-size:0.66rem; color:var(--text-dim);
    letter-spacing:0.12em; text-transform:uppercase; margin-bottom:9px;
  }}
  .chips {{ display:flex; flex-wrap:wrap; gap:7px; }}
  .chip {{
    background: rgba(13,48,96,0.55);
    border: 1px solid rgba(200,168,75,0.3);
    color: var(--ice); padding: 5px 13px;
    border-radius: 20px; font-size: 0.76rem;
    cursor: pointer; white-space: nowrap;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.2s ease;
  }}
  .chip:hover {{
    background: rgba(200,168,75,0.12);
    border-color: var(--gold); color: var(--gold-light);
    transform: translateY(-2px);
    box-shadow: 0 5px 14px rgba(200,168,75,0.18);
  }}

  /* ── Messages ── */
  #messages {{
    flex: 1; overflow-y: auto;
    padding: 14px 0; display:flex; flex-direction:column; gap:14px;
    scroll-behavior: smooth;
  }}
  #messages::-webkit-scrollbar {{ width:3px; }}
  #messages::-webkit-scrollbar-thumb {{ background:rgba(168,216,240,0.12); border-radius:2px; }}

  .row {{
    display:flex; align-items:flex-end; gap:9px;
    animation: sup 0.38s cubic-bezier(0.22,1,0.36,1) both;
  }}
  .row.user {{ flex-direction:row-reverse; }}
  @keyframes sup {{
    from {{ opacity:0; transform:translateY(16px); }}
    to   {{ opacity:1; transform:translateY(0); }}
  }}

  .av {{
    width:30px; height:30px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:14px; flex-shrink:0;
  }}
  .av.bot {{
    background:linear-gradient(135deg,var(--wave),var(--foam));
    border:1.5px solid rgba(200,168,75,0.6);
    box-shadow:0 0 10px rgba(200,168,75,0.2);
  }}
  .av.user {{
    background:linear-gradient(135deg,#1a4a7a,#1060a0);
    border:1.5px solid rgba(122,174,200,0.5);
  }}

  .bub {{
    max-width:74%; padding:11px 15px;
    border-radius:var(--radius); font-size:0.875rem; line-height:1.65;
  }}
  .bub.bot {{
    background:rgba(10,32,64,0.82);
    border:1px solid rgba(13,48,96,0.9);
    border-bottom-left-radius:4px;
    backdrop-filter:blur(14px);
    color:var(--text);
  }}
  .bub.user {{
    background:linear-gradient(135deg,#0d4070,#0a5090);
    border:1px solid rgba(26,80,140,0.5);
    border-bottom-right-radius:4px;
    color:#e8f4ff;
  }}

  .chart-img {{
    width:100%; margin-top:10px;
    border-radius:10px;
    border:1px solid rgba(200,168,75,0.18);
    display:block;
  }}

  /* Typing dots */
  .tdots {{ display:flex; align-items:center; gap:5px; padding:6px 2px; }}
  .td {{
    width:7px; height:7px; border-radius:50%;
    background:var(--mist);
    animation:tb 1.3s ease-in-out infinite;
  }}
  .td:nth-child(2){{animation-delay:.16s}} .td:nth-child(3){{animation-delay:.32s}}
  @keyframes tb {{
    0%,60%,100%{{transform:translateY(0);opacity:0.35}}
    30%{{transform:translateY(-7px);opacity:1}}
  }}

  /* Divider */
  .dvd {{
    text-align:center; font-size:0.65rem; color:var(--text-dim);
    letter-spacing:0.1em; text-transform:uppercase;
    display:flex; align-items:center; gap:10px;
  }}
  .dvd::before,.dvd::after {{ content:''; flex:1; height:1px; background:rgba(200,168,75,0.13); }}

  /* ── Input ── */
  .inp-area {{ padding:12px 0 18px; flex-shrink:0; border-top:1px solid rgba(200,168,75,0.1); }}
  .inp-row {{
    display:flex; align-items:center; gap:9px;
    background:rgba(10,32,64,0.65);
    border:1px solid rgba(200,168,75,0.22);
    border-radius:26px; padding:7px 7px 7px 17px;
    backdrop-filter:blur(12px);
    transition:border-color .2s, box-shadow .2s;
  }}
  .inp-row:focus-within {{
    border-color:rgba(200,168,75,0.5);
    box-shadow:0 0 22px rgba(200,168,75,0.1);
  }}
  #ci {{
    flex:1; background:transparent; border:none; outline:none;
    color:var(--text); font-size:0.88rem;
    font-family:'DM Sans',sans-serif;
    resize:none; max-height:110px; min-height:22px; line-height:1.55;
  }}
  #ci::placeholder {{ color:var(--text-dim); }}
  .sbtn {{
    width:38px; height:38px; border-radius:50%; flex-shrink:0;
    background:linear-gradient(135deg,var(--gold),var(--copper));
    border:none; cursor:pointer;
    display:flex; align-items:center; justify-content:center;
    font-size:15px; transition:all .2s;
    box-shadow:0 2px 10px rgba(200,168,75,0.25);
  }}
  .sbtn:hover {{ transform:scale(1.1); box-shadow:0 5px 18px rgba(200,168,75,0.4); }}
  .sbtn:active {{ transform:scale(0.94); }}
  .sbtn:disabled {{ opacity:0.35; cursor:not-allowed; transform:none; box-shadow:none; }}

  .clr {{
    display:block; margin:9px auto 0;
    background:transparent; border:1px solid rgba(168,216,240,0.12);
    color:var(--text-dim); font-size:0.7rem; padding:3px 13px;
    border-radius:10px; cursor:pointer;
    font-family:'DM Sans',sans-serif; transition:all .2s; letter-spacing:.05em;
  }}
  .clr:hover {{ border-color:rgba(192,80,74,0.45); color:#e07070; }}

  /* Toast */
  #toast {{
    position:fixed; bottom:85px; left:50%; transform:translateX(-50%) translateY(8px);
    background:rgba(192,80,74,0.92); color:#fff;
    padding:9px 20px; border-radius:18px; font-size:0.8rem;
    backdrop-filter:blur(10px); z-index:200;
    opacity:0; pointer-events:none; transition:all .3s ease;
  }}
  #toast.show {{ opacity:1; transform:translateX(-50%) translateY(0); }}
</style>
</head>
<body>

<!-- Particles -->
<div class="p" style="width:3px;height:3px;left:12%;animation-duration:20s;animation-delay:0s"></div>
<div class="p" style="width:2px;height:2px;left:32%;animation-duration:26s;animation-delay:5s"></div>
<div class="p" style="width:4px;height:4px;left:58%;animation-duration:22s;animation-delay:10s"></div>
<div class="p" style="width:2px;height:2px;left:76%;animation-duration:18s;animation-delay:3s"></div>
<div class="p" style="width:3px;height:3px;left:88%;animation-duration:24s;animation-delay:14s"></div>
<div class="p" style="width:2px;height:2px;left:44%;animation-duration:30s;animation-delay:7s"></div>

<div class="shell">

  <!-- Header -->
  <div class="hdr">
    <div class="hdr-icon">🚢</div>
    <div class="hdr-copy">
      <h1>Titanic Data Analyst</h1>
      <p>R.M.S. Titanic &middot; April 1912 &middot; 2,224 souls aboard</p>
    </div>
    <div class="hdr-status">
      <div class="dot" id="dot"></div>
      <span id="status-label">online</span>
    </div>
  </div>

  <!-- Chips -->
  <div id="chips-wrap">
    <div class="chips-label">Ask the manifest</div>
    <div class="chips">
      <span class="chip" tabindex="0">What % of passengers were male?</span>
      <span class="chip" tabindex="0">Show a histogram of passenger ages</span>
      <span class="chip" tabindex="0">What was the average ticket fare?</span>
      <span class="chip" tabindex="0">Passengers per embarkation port</span>
      <span class="chip" tabindex="0">What was the survival rate?</span>
      <span class="chip" tabindex="0">Show survival by passenger class</span>
    </div>
  </div>

  <!-- Messages -->
  <div id="messages">
    <div class="dvd">Begin your inquiry</div>
  </div>

  <!-- Input -->
  <div class="inp-area">
    <div class="inp-row">
      <textarea id="ci" rows="1" placeholder="Ask me anything about the Titanic passengers…"></textarea>
      <button class="sbtn" id="sb" title="Send">&#10148;</button>
    </div>
    <button class="clr" id="clr-btn">&#9875; Clear voyage log</button>
  </div>

</div>

<div id="toast"></div>

<script>
  const API = "{BACKEND_URL}";
  let history = [];
  let busy = false;
  let typN = 0;

  // Health check
  async function ping() {{
    try {{
      const r = await fetch(API + "/health", {{signal: AbortSignal.timeout(4000)}});
      const ok = r.ok;
      document.getElementById("dot").className = ok ? "dot" : "dot off";
      document.getElementById("status-label").textContent = ok ? "online" : "offline";
    }} catch {{ 
      document.getElementById("dot").className = "dot off";
      document.getElementById("status-label").textContent = "offline";
    }}
  }}
  ping(); setInterval(ping, 15000);

  // ── Wire up all interactions after DOM ready ──────────────────────────────
  const ci = document.getElementById("ci");

  // Auto-resize textarea
  ci.addEventListener("input", () => {{
    ci.style.height = "auto";
    ci.style.height = Math.min(ci.scrollHeight, 110) + "px";
  }});

  // Enter key — use capture:true so we intercept BEFORE Streamlit parent frame
  ci.addEventListener("keydown", function(e) {{
    if (e.key === "Enter" && !e.shiftKey) {{
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      send();
    }}
  }}, true);

  // Send button
  document.getElementById("sb").addEventListener("click", function(e) {{
    e.preventDefault();
    e.stopPropagation();
    send();
  }});

  // Clear button
  document.getElementById("clr-btn").addEventListener("click", function(e) {{
    e.preventDefault();
    clearChat();
  }});

  // Chip clicks — wire up after DOM is ready
  document.querySelectorAll(".chip").forEach(function(chip) {{
    chip.addEventListener("click", function(e) {{
      e.stopPropagation();
      ci.value = chip.textContent.trim();
      send();
    }});
    // Also allow Enter key on focused chips for accessibility
    chip.addEventListener("keydown", function(e) {{
      if (e.key === "Enter" || e.key === " ") {{
        e.preventDefault();
        ci.value = chip.textContent.trim();
        send();
      }}
    }});
  }});

  async function send() {{
    const q = ci.value.trim();
    if (!q || busy) return;

    // Hide chips on first message
    const cw = document.getElementById("chips-wrap");
    if (cw) cw.style.display = "none";

    ci.value = ""; ci.style.height = "auto";
    setBusy(true);

    addMsg("user", q);
    history.push({{role:"user", content:q}});
    const tid = addTyping();

    try {{
      const res = await fetch(API + "/chat", {{
        method: "POST",
        headers: {{"Content-Type":"application/json"}},
        body: JSON.stringify({{
          question: q,
          history: history.slice(0, -1)
        }}),
        signal: AbortSignal.timeout(60000)
      }});

      removeTyping(tid);

      if (!res.ok) {{
        toast("Server error " + res.status);
        addMsg("bot", "I encountered an error — please try again.");
        return;
      }}

      const d = await res.json();
      const ans = d.answer || "No response received.";
      addMsg("bot", ans, d.chart_base64 || null);
      history.push({{role:"assistant", content:ans}});

    }} catch(e) {{
      removeTyping(tid);
      if (e.name === "TimeoutError") {{
        toast("Request timed out — please retry.");
        addMsg("bot", "The request timed out. Please try again.");
      }} else {{
        toast("Cannot reach backend.");
        addMsg("bot", "Could not connect to the backend. Please wait and retry.");
      }}
    }} finally {{
      setBusy(false);
    }}
  }}

  function addMsg(role, text, chart=null) {{
    const msgs = document.getElementById("messages");
    const row = document.createElement("div");
    row.className = "row " + role;

    const av = document.createElement("div");
    av.className = "av " + (role==="user" ? "user" : "bot");
    av.textContent = role==="user" ? "👤" : "⚓";

    const bub = document.createElement("div");
    bub.className = "bub " + (role==="user" ? "user" : "bot");

    // Render markdown bold + line breaks
    bub.innerHTML = text
      .replace(/[*][*](.*?)[*][*]/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");

    if (chart) {{
      const img = document.createElement("img");
      img.className = "chart-img";
      img.src = "data:image/png;base64," + chart;
      img.alt = "Chart";
      bub.appendChild(img);
    }}

    row.appendChild(role==="user" ? bub : av);
    row.appendChild(role==="user" ? av : bub);
    msgs.appendChild(row);
    msgs.scrollTop = msgs.scrollHeight;
  }}

  function addTyping() {{
    const id = "t" + (++typN);
    const msgs = document.getElementById("messages");
    const row = document.createElement("div"); row.className="row"; row.id=id;
    const av = document.createElement("div"); av.className="av bot"; av.textContent="⚓";
    const bub = document.createElement("div"); bub.className="bub bot";
    bub.innerHTML='<div class="tdots"><div class="td"></div><div class="td"></div><div class="td"></div></div>';
    row.appendChild(av); row.appendChild(bub);
    msgs.appendChild(row);
    msgs.scrollTop = msgs.scrollHeight;
    return id;
  }}

  function removeTyping(id) {{ const el=document.getElementById(id); if(el) el.remove(); }}

  function setBusy(v) {{
    busy=v;
    const b=document.getElementById("sb");
    b.disabled=v; b.innerHTML=v?"&#8987;":"&#10148;";
    ci.disabled=v;
  }}

  function clearChat() {{
    history=[];
    document.getElementById("messages").innerHTML='<div class="dvd">Begin your inquiry</div>';
    const cw=document.getElementById("chips-wrap");
    if(cw) cw.style.display="block";
  }}

  function toast(msg) {{
    const t=document.getElementById("toast");
    t.textContent=msg; t.classList.add("show");
    setTimeout(()=>t.classList.remove("show"), 4000);
  }}
</script>
</body>
</html>"""

# ── Render — height should fill the viewport comfortably ────────────────────
import streamlit.components.v1 as components
components.html(CHAT_UI, height=820, scrolling=False)