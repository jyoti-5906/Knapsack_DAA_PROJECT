"""
KnapsackLab - DAA Project
Run with:  python app.py
Then open: http://localhost:8000   (opens automatically)

Uses ONLY the Python standard library - nothing to install.
"""
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8000


# ----------------------------------------------------------------------
#  ALGORITHMS
# ----------------------------------------------------------------------
def fractional_knapsack(items, capacity):
    """Greedy: sort by profit/weight, take whole items, then a fraction."""
    order = sorted(range(len(items)),
                   key=lambda i: items[i]["profit"] / items[i]["weight"],
                   reverse=True)
    remaining = capacity
    total = 0.0
    steps = []
    for i in order:
        it = items[i]
        ratio = it["profit"] / it["weight"]
        if remaining <= 0:
            frac = 0.0
        elif it["weight"] <= remaining:
            frac = 1.0
        else:
            frac = remaining / it["weight"]
        used = frac * it["weight"]
        gain = frac * it["profit"]
        remaining -= used
        total += gain
        steps.append({
            "index": i, "name": it["name"], "weight": it["weight"],
            "profit": it["profit"], "ratio": ratio, "fraction": frac,
            "weight_used": used, "gain": gain,
        })
    return {"total": total, "steps": steps, "weight_used": capacity - remaining}


def zero_one_knapsack(items, capacity):
    """Dynamic programming: dp[i][w] = best profit with first i items, capacity w."""
    n = len(items)
    dp = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wt, pr = items[i - 1]["weight"], items[i - 1]["profit"]
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if wt <= w and dp[i - 1][w - wt] + pr > dp[i][w]:
                dp[i][w] = dp[i - 1][w - wt] + pr

    chosen, w = [], capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            chosen.append(i - 1)
            w -= items[i - 1]["weight"]
    chosen.reverse()

    result = {
        "total": dp[n][capacity],
        "chosen": [dict(items[i], index=i) for i in chosen],
        "weight_used": sum(items[i]["weight"] for i in chosen),
        "table": None,
    }
    if n <= 12 and capacity <= 25:
        result["table"] = dp
    return result


def solve(payload):
    items = payload.get("items", [])
    if not items:
        raise ValueError("Add at least one product.")
    clean = []
    for it in items:
        name = str(it.get("name", "")).strip() or "Item"
        weight = float(it["weight"])
        profit = float(it["profit"])
        if weight <= 0 or weight != int(weight):
            raise ValueError(f"Weight of '{name}' must be a positive whole number.")
        if profit < 0:
            raise ValueError(f"Profit of '{name}' cannot be negative.")
        clean.append({"name": name, "weight": int(weight), "profit": profit})

    cap = float(payload.get("capacity", 0))
    if cap <= 0 or cap != int(cap):
        raise ValueError("Knapsack capacity must be a positive whole number.")
    cap = int(cap)
    if cap > 5000 or len(clean) > 200:
        raise ValueError("Too large: use capacity <= 5000 and at most 200 products.")

    return {
        "fractional": fractional_knapsack(clean, cap),
        "zero_one": zero_one_knapsack(clean, cap),
    }


# ----------------------------------------------------------------------
#  WEBSITE
# ----------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KnapsackLab | Fill the bag, max the profit</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎒</text></svg>">
<style>
  :root{
    --bg:#fff7e8; --ink:#14142b; --white:#fff;
    --yellow:#ffd23f; --purple:#8b5cf6; --pink:#ff6b9d; --green:#22c55e; --orange:#fb923c; --blue:#38bdf8;
    --line:3px solid var(--ink);
    --shadow:6px 6px 0 var(--ink);
    --shadow-s:4px 4px 0 var(--ink);
    --r:18px;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth;scroll-padding-top:90px}
  body{font-family:"Trebuchet MS","Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5;overflow-x:hidden;
       background-image:radial-gradient(rgba(20,20,43,.12) 1.5px,transparent 1.5px);background-size:26px 26px}
  a{color:inherit;text-decoration:none}
  .wrap{max-width:1140px;margin:0 auto;padding:0 22px}

  /* ---------- NAVBAR ---------- */
  nav{position:sticky;top:0;z-index:50;background:var(--white);border-bottom:var(--line)}
  nav .wrap{display:flex;align-items:center;justify-content:space-between;height:70px}
  .logo{font-size:1.45rem;font-weight:900;display:flex;align-items:center;gap:10px;letter-spacing:-.02em}
  .logo i{font-style:normal;background:var(--yellow);border:var(--line);border-radius:12px;width:42px;height:42px;display:grid;place-items:center;box-shadow:3px 3px 0 var(--ink)}
  .links{display:flex;align-items:center;gap:8px}
  .links a.l{font-weight:700;padding:9px 16px;border-radius:99px;transition:.15s}
  .links a.l:hover{background:var(--yellow)}
  .btn{display:inline-block;font:inherit;font-weight:800;font-size:1rem;cursor:pointer;color:var(--ink);background:var(--yellow);border:var(--line);border-radius:14px;padding:12px 24px;box-shadow:var(--shadow-s);transition:transform .12s,box-shadow .12s}
  .btn:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--ink)}
  .btn:active{transform:translate(3px,3px);box-shadow:1px 1px 0 var(--ink)}
  .btn.purple{background:var(--purple);color:#fff}
  .btn.green{background:var(--green)}
  .btn.white{background:var(--white)}
  @media(max-width:620px){.links a.l{display:none}}

  /* ---------- HERO ---------- */
  .hero{padding:70px 0 80px}
  .hero .wrap{display:grid;grid-template-columns:1.1fr 1fr;gap:40px;align-items:center}
  @media(max-width:900px){.hero .wrap{grid-template-columns:1fr}.visual{display:none}}
  .sticker{display:inline-block;background:var(--pink);color:#fff;font-weight:800;font-size:.9rem;padding:7px 16px;border:var(--line);border-radius:99px;transform:rotate(-2deg);box-shadow:3px 3px 0 var(--ink);margin-bottom:22px}
  .hero h1{font-size:clamp(2.6rem,6.2vw,4.6rem);line-height:1.02;font-weight:900;letter-spacing:-.03em;margin-bottom:20px}
  .hl{background:var(--yellow);padding:0 10px;border:var(--line);border-radius:12px;display:inline-block;transform:rotate(-1.5deg);box-shadow:4px 4px 0 var(--ink)}
  .hero p.one{font-size:1.2rem;max-width:520px;margin-bottom:30px;font-weight:500}
  .hero p.one b{background:linear-gradient(transparent 60%,rgba(255,107,157,.55) 60%)}
  .cta{display:flex;gap:14px;flex-wrap:wrap}

  .visual{position:relative;height:420px}
  .bag{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:11rem;filter:drop-shadow(8px 8px 0 rgba(20,20,43,.9));animation:bob 4s ease-in-out infinite}
  @keyframes bob{50%{transform:translate(-50%,-56%)}}
  .fc{position:absolute;background:var(--white);border:var(--line);border-radius:16px;padding:12px 16px;font-weight:800;box-shadow:var(--shadow-s);display:flex;gap:10px;align-items:center;animation:float 5s ease-in-out infinite}
  .fc small{display:block;font-weight:600;opacity:.65;font-size:.75rem}
  .fc .e{font-size:1.8rem}
  .fc1{top:6%;left:0;transform:rotate(-6deg);background:var(--blue)}
  .fc2{top:14%;right:0;transform:rotate(5deg);background:var(--green);animation-delay:-1.5s}
  .fc3{bottom:8%;left:6%;transform:rotate(4deg);background:var(--orange);animation-delay:-3s}
  .fc4{bottom:14%;right:2%;transform:rotate(-4deg);background:var(--pink);color:#fff;animation-delay:-2s}
  @keyframes float{50%{margin-top:-12px}}

  /* ---------- TICKER ---------- */
  .ticker{background:var(--ink);color:var(--yellow);border-top:var(--line);border-bottom:var(--line);overflow:hidden;white-space:nowrap;padding:14px 0;font-weight:900;font-size:1.2rem;letter-spacing:.05em}
  .ticker div{display:inline-block;animation:slide 22s linear infinite}
  @keyframes slide{to{transform:translateX(-50%)}}

  /* ---------- SOLVER ---------- */
  section{padding:80px 0}
  .title{text-align:center;margin-bottom:44px}
  .title h2{font-size:clamp(2rem,4.5vw,3rem);font-weight:900;letter-spacing:-.02em}
  .title p{margin-top:8px;font-weight:500;font-size:1.05rem}
  .card{background:var(--white);border:var(--line);border-radius:var(--r);padding:26px;box-shadow:var(--shadow)}
  .card h3{font-size:1.3rem;font-weight:900;margin-bottom:18px;display:flex;align-items:center;gap:10px}
  .num{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--purple);color:#fff;border:var(--line);font-size:1rem}
  .grid{display:grid;grid-template-columns:1.4fr 1fr;gap:28px;align-items:start}
  @media(max-width:900px){.grid{grid-template-columns:1fr}}

  .form{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;align-items:end}
  @media(max-width:640px){.form{grid-template-columns:1fr 1fr}.form .nm{grid-column:1/-1}}
  label{display:block;font-size:.78rem;font-weight:900;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
  input{width:100%;font:inherit;font-weight:600;font-size:1rem;padding:12px 14px;border:var(--line);border-radius:12px;background:#fffdf7;color:var(--ink);transition:.12s}
  input:focus{outline:none;background:#fff;box-shadow:var(--shadow-s);transform:translate(-2px,-2px)}
  .form .btn{padding:12px 22px}

  .list{margin-top:22px;display:flex;flex-direction:column;gap:12px;max-height:340px;overflow-y:auto;padding:4px 8px 8px 4px}
  .item{display:flex;align-items:center;gap:12px;padding:12px 14px;border:var(--line);border-radius:14px;background:var(--white);box-shadow:3px 3px 0 var(--ink);animation:pop .3s}
  @keyframes pop{from{opacity:0;transform:scale(.9) rotate(-2deg)}to{opacity:1;transform:none}}
  .dot{width:16px;height:16px;border-radius:50%;border:2px solid var(--ink);flex:none}
  .item .n{font-weight:800;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .chip{font-size:.78rem;font-weight:800;padding:4px 11px;border:2px solid var(--ink);border-radius:99px;background:#fffdf7;white-space:nowrap}
  .chip.p{background:#bbf7d0}
  .chip.r{background:#e9d5ff}
  .x{font:inherit;font-weight:900;cursor:pointer;width:30px;height:30px;border-radius:50%;border:2px solid var(--ink);background:var(--white);transition:.12s}
  .x:hover{background:var(--pink);color:#fff}
  .empty{text-align:center;font-weight:700;padding:30px 10px;border:3px dashed var(--ink);border-radius:14px;background:#fffdf7}
  .quick{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
  .quick .btn{padding:9px 18px;font-size:.9rem;box-shadow:3px 3px 0 var(--ink)}

  .side{display:flex;flex-direction:column;gap:20px}
  .cap input{font-size:2.4rem;font-weight:900;text-align:center;padding:18px;background:var(--yellow)}
  .cap input:focus{background:#ffe066}
  .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .stat{border:var(--line);border-radius:14px;padding:12px 6px;text-align:center;box-shadow:3px 3px 0 var(--ink)}
  .stat:nth-child(1){background:#bae6fd}.stat:nth-child(2){background:#fed7aa}.stat:nth-child(3){background:#bbf7d0}
  .stat b{display:block;font-size:1.5rem;font-weight:900;line-height:1.1}
  .stat span{font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em}
  .solve{width:100%;font-size:1.25rem;padding:18px;background:var(--green)}
  .error{display:none;background:#fecdd3;border:var(--line);border-radius:12px;padding:10px 14px;font-weight:700}

  /* ---------- RESULTS ---------- */
  #results{display:none;margin-top:60px}
  .win{display:flex;align-items:center;gap:16px;padding:18px 24px;border:var(--line);border-radius:var(--r);background:var(--purple);color:#fff;font-weight:700;font-size:1.05rem;box-shadow:var(--shadow);margin-bottom:30px}
  .win .em{font-size:2.2rem}
  .res{display:grid;grid-template-columns:1fr 1fr;gap:28px}
  @media(max-width:900px){.res{grid-template-columns:1fr}}
  .res .card.f{background:#fff1d6}
  .res .card.z{background:#d9f7e4}
  .tagline{display:inline-block;font-weight:900;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;padding:5px 14px;border:2px solid var(--ink);border-radius:99px;background:var(--white);margin-bottom:12px}
  .res h3{font-size:1.5rem;margin-bottom:6px}
  .res .one{font-weight:600;font-size:.95rem;margin-bottom:16px}
  .big{font-size:3.6rem;font-weight:900;line-height:1;letter-spacing:-.03em}
  .big small{font-size:1rem;font-weight:800;letter-spacing:0;margin-left:6px}
  .bar{display:flex;height:36px;border:var(--line);border-radius:99px;overflow:hidden;background:var(--white);margin:18px 0 8px}
  .seg{height:100%;width:0;transition:width 1s cubic-bezier(.2,.8,.2,1);display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:900;color:var(--ink);overflow:hidden;white-space:nowrap;border-right:2px solid var(--ink)}
  .seg:last-child{border-right:0}
  .capl{display:flex;justify-content:space-between;font-weight:800;font-size:.82rem;margin-bottom:18px}
  .rows{display:flex;flex-direction:column;gap:10px}
  .rrow{display:flex;align-items:center;gap:10px;background:var(--white);border:2px solid var(--ink);border-radius:12px;padding:9px 12px;font-weight:700}
  .rrow .n{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .tag{font-size:.74rem;font-weight:900;padding:3px 11px;border:2px solid var(--ink);border-radius:99px}
  .t-full{background:#86efac}.t-part{background:var(--yellow)}.t-none{background:#e5e7eb}
  .g{font-weight:900;min-width:52px;text-align:right}
  details{margin-top:34px}
  summary{cursor:pointer;font-weight:900;font-size:1.05rem;padding:14px 22px;background:var(--white);border:var(--line);border-radius:14px;box-shadow:var(--shadow-s);list-style:none}
  summary::-webkit-details-marker{display:none}
  .dpw{overflow-x:auto;margin-top:18px;background:var(--white);border:var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow-s)}
  table.dp{border-collapse:collapse;margin:auto;font-size:.85rem;font-weight:700}
  .dp th,.dp td{padding:6px 11px;text-align:center;border:2px solid var(--ink)}
  .dp th{background:var(--yellow)}
  .dp td.pick{background:#86efac;font-weight:900}

  footer{background:var(--ink);color:#fff;text-align:center;padding:30px 0;font-weight:700;border-top:var(--line)}
  footer span{color:var(--yellow)}
</style>
</head>
<body>

<nav>
  <div class="wrap">
    <a href="#home" class="logo"><i>🎒</i>KnapsackLab</a>
    <div class="links">
      <a class="l" href="#home">Home</a>
      <a class="l" href="#solver">Solver</a>
      <a class="btn" href="#solver">Try it free</a>
    </div>
  </div>
</nav>

<!-- HERO -->
<header class="hero" id="home">
  <div class="wrap">
    <div>
      <span class="sticker">DAA Project ✨</span>
      <h1>Fill the bag.<br>Max the <span class="hl">profit!</span></h1>
      <p class="one"><b>Fractional</b> (Greedy) lets you split items, while <b>0/1</b> (Dynamic Programming) takes each item whole or not at all.</p>
      <div class="cta">
        <a href="#solver" class="btn purple">Start solving →</a>
        <a href="#solver" class="btn white" onclick="loadExample()">Try an example</a>
      </div>
    </div>
    <div class="visual">
      <div class="bag">🎒</div>
      <div class="fc fc1"><span class="e">💻</span><div>Laptop<small>w 10 · ₹60</small></div></div>
      <div class="fc fc2"><span class="e">📷</span><div>Camera<small>w 20 · ₹100</small></div></div>
      <div class="fc fc3"><span class="e">📚</span><div>Books<small>w 30 · ₹120</small></div></div>
      <div class="fc fc4"><span class="e">💰</span><div>Max profit<small>you decide</small></div></div>
    </div>
  </div>
</header>

<div class="ticker"><div>
  FRACTIONAL ★ GREEDY ★ 0/1 KNAPSACK ★ DYNAMIC PROGRAMMING ★ MAX PROFIT ★ FRACTIONAL ★ GREEDY ★ 0/1 KNAPSACK ★ DYNAMIC PROGRAMMING ★ MAX PROFIT ★
  FRACTIONAL ★ GREEDY ★ 0/1 KNAPSACK ★ DYNAMIC PROGRAMMING ★ MAX PROFIT ★ FRACTIONAL ★ GREEDY ★ 0/1 KNAPSACK ★ DYNAMIC PROGRAMMING ★ MAX PROFIT ★
</div></div>

<!-- SOLVER -->
<section id="solver">
  <div class="wrap">
    <div class="title">
      <h2>Try the solver 🚀</h2>
      <p>Add products, set the limit, hit solve.</p>
    </div>

    <div class="grid">
      <div class="card">
        <h3><span class="num">1</span> Add your products</h3>
        <div class="form">
          <div class="nm"><label>Name</label><input id="name" placeholder="Laptop"></div>
          <div><label>Weight</label><input id="weight" type="number" min="1" step="1" placeholder="10"></div>
          <div><label>Profit</label><input id="profit" type="number" min="0" step="any" placeholder="60"></div>
          <button class="btn" onclick="addItem()">+ Add</button>
        </div>
        <div class="list" id="list"></div>
        <div class="quick">
          <button class="btn white" onclick="loadExample()">⚡ Example</button>
          <button class="btn white" onclick="clearAll()">🗑 Clear</button>
        </div>
      </div>

      <div class="side">
        <div class="card cap">
          <h3><span class="num">2</span> Bag capacity</h3>
          <label>Max weight it can hold</label>
          <input id="capacity" type="number" min="1" step="1" placeholder="50">
        </div>
        <div class="stats">
          <div class="stat"><b id="s-count">0</b><span>Products</span></div>
          <div class="stat"><b id="s-weight">0</b><span>Weight</span></div>
          <div class="stat"><b id="s-profit">0</b><span>Profit</span></div>
        </div>
        <div class="error" id="error"></div>
        <button class="btn solve" onclick="solve()">Solve it! 🚀</button>
      </div>
    </div>

    <!-- RESULTS -->
    <div id="results">
      <div class="win" id="win"></div>
      <div class="res">
        <div class="card f">
          <span class="tagline">Greedy</span>
          <h3>Fractional Knapsack</h3>
          <p class="one">Best profit per weight first, and the last item can be cut.</p>
          <div class="big"><span id="f-total"></span><small>profit</small></div>
          <div class="bar" id="f-bar"></div>
          <div class="capl"><span id="f-used"></span><span id="f-cap"></span></div>
          <div class="rows" id="f-rows"></div>
        </div>
        <div class="card z">
          <span class="tagline">Dynamic Programming</span>
          <h3>0/1 Knapsack</h3>
          <p class="one">Every item is taken whole or skipped, and a table finds the best mix.</p>
          <div class="big"><span id="z-total"></span><small>profit</small></div>
          <div class="bar" id="z-bar"></div>
          <div class="capl"><span id="z-used"></span><span id="z-cap"></span></div>
          <div class="rows" id="z-rows"></div>
        </div>
      </div>
      <details id="dp-det" style="display:none">
        <summary>📊 Show the DP table</summary>
        <div class="dpw"><table class="dp" id="dp-table"></table></div>
      </details>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">Made for the <span>DAA</span> project · Python + JavaScript</div>
</footer>

<script>
const COLORS = ['#38bdf8','#ff6b9d','#ffd23f','#22c55e','#8b5cf6','#fb923c','#2dd4bf','#f87171','#a3e635','#c084fc'];
const col = i => COLORS[i % COLORS.length];
let items = [];
const $ = id => document.getElementById(id);
const fmt = n => Number.isInteger(n) ? String(n) : (+n).toFixed(2);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function showError(msg){ const e = $('error'); e.textContent = msg; e.style.display = msg ? 'block' : 'none'; }

function addItem(){
  const name = $('name').value.trim() || ('Item ' + (items.length + 1));
  const weight = parseFloat($('weight').value);
  const profit = parseFloat($('profit').value);
  if (!(weight > 0) || !Number.isInteger(weight)) return showError('Weight must be a positive whole number.');
  if (isNaN(profit) || profit < 0) return showError('Enter a valid profit (0 or more).');
  showError('');
  items.push({name, weight, profit});
  $('name').value = $('weight').value = $('profit').value = '';
  $('name').focus();
  renderItems();
}
function removeItem(i){ items.splice(i, 1); renderItems(); }
function clearAll(){ items = []; renderItems(); $('results').style.display = 'none'; }
function loadExample(){
  items = [
    {name:'Laptop', weight:10, profit:60},
    {name:'Camera', weight:20, profit:100},
    {name:'Books',  weight:30, profit:120},
  ];
  $('capacity').value = 50;
  showError('');
  renderItems();
}

function renderItems(){
  const L = $('list');
  if (!items.length) L.innerHTML = '<div class="empty">Your bag is empty 🎒<br>Add a product or try the example.</div>';
  else L.innerHTML = items.map((it, i) => `
    <div class="item">
      <span class="dot" style="background:${col(i)}"></span>
      <span class="n">${esc(it.name)}</span>
      <span class="chip">⚖ ${fmt(it.weight)}</span>
      <span class="chip p">₹ ${fmt(it.profit)}</span>
      <span class="chip r">${fmt(+(it.profit / it.weight).toFixed(2))}/kg</span>
      <button class="x" onclick="removeItem(${i})" title="Remove">✕</button>
    </div>`).join('');
  $('s-count').textContent = items.length;
  $('s-weight').textContent = fmt(items.reduce((a, b) => a + b.weight, 0));
  $('s-profit').textContent = fmt(items.reduce((a, b) => a + b.profit, 0));
}
['name','weight','profit'].forEach(id => $(id).addEventListener('keydown', e => { if (e.key === 'Enter') addItem(); }));
$('capacity').addEventListener('keydown', e => { if (e.key === 'Enter') solve(); });

async function solve(){
  showError('');
  const capacity = parseFloat($('capacity').value);
  if (!items.length) return showError('Please add at least one product.');
  if (!(capacity > 0)) return showError('Please enter the bag capacity.');
  try{
    const res = await fetch('/solve', {method:'POST', headers:{'Content-Type':'application/json'},
                                       body: JSON.stringify({items, capacity})});
    const data = await res.json();
    if (!res.ok) return showError(data.error || 'Something went wrong.');
    render(data, capacity);
  }catch(e){ showError('Could not reach the server. Is app.py still running?'); }
}

function segBar(el, parts, cap){
  el.innerHTML = parts.map(p => `<div class="seg" data-w="${p.w / cap * 100}" style="background:${col(p.index)}" title="${esc(p.name)}">${esc(p.name)}</div>`).join('');
  requestAnimationFrame(() => requestAnimationFrame(() =>
    el.querySelectorAll('.seg').forEach(s => s.style.width = s.dataset.w + '%')));
}

function tag(f){
  if (f >= 1) return '<span class="tag t-full">FULL</span>';
  if (f > 0)  return `<span class="tag t-part">${(f * 100).toFixed(0)}%</span>`;
  return '<span class="tag t-none">SKIPPED</span>';
}

function render(d, cap){
  const f = d.fractional, z = d.zero_one;

  $('f-total').textContent = fmt(+f.total.toFixed(2));
  $('z-total').textContent = fmt(+z.total.toFixed(2));
  $('f-used').textContent = `Used ${fmt(f.weight_used)}`;
  $('z-used').textContent = `Used ${fmt(z.weight_used)}`;
  $('f-cap').textContent = $('z-cap').textContent = `Capacity ${cap}`;

  segBar($('f-bar'), f.steps.filter(s => s.fraction > 0).map(s => ({index:s.index, name:s.name, w:s.weight_used})), cap);
  segBar($('z-bar'), z.chosen.map(c => ({index:c.index, name:c.name, w:c.weight})), cap);

  $('f-rows').innerHTML = f.steps.map(s => `
    <div class="rrow"><span class="dot" style="background:${col(s.index)}"></span>
      <span class="n">${esc(s.name)}</span>${tag(s.fraction)}
      <span class="g">+${fmt(+s.gain.toFixed(2))}</span></div>`).join('');

  $('z-rows').innerHTML = z.chosen.length
    ? z.chosen.map(c => `
      <div class="rrow"><span class="dot" style="background:${col(c.index)}"></span>
        <span class="n">${esc(c.name)}</span><span class="tag t-full">TAKEN</span>
        <span class="g">+${fmt(c.profit)}</span></div>`).join('')
    : '<div class="empty">No item fits in the bag.</div>';

  const diff = f.total - z.total;
  $('win').innerHTML = diff > 1e-9
    ? `<span class="em">🍊</span><span>Fractional wins by <b>${fmt(+diff.toFixed(2))}</b> because it can cut an item to fill the bag.</span>`
    : `<span class="em">🤝</span><span>It's a tie! Both methods give the <b>same profit</b> here.</span>`;

  const det = $('dp-det');
  if (z.table){
    const path = new Set(); let w = cap;
    for (let i = items.length; i > 0; i--){
      if (z.table[i][w] !== z.table[i-1][w]){ path.add(i + ',' + w); w -= items[i-1].weight; }
    }
    let h = '<tr><th>Item \\ Cap</th>' + Array.from({length: cap + 1}, (_, c) => `<th>${c}</th>`).join('') + '</tr>';
    z.table.forEach((row, i) => {
      h += `<tr><th>${i === 0 ? '—' : esc(items[i-1].name)}</th>` +
        row.map((v, c) => `<td class="${path.has(i + ',' + c) ? 'pick' : ''}">${fmt(+v.toFixed(2))}</td>`).join('') + '</tr>';
    });
    $('dp-table').innerHTML = h;
    det.style.display = 'block';
  } else det.style.display = 'none';

  $('results').style.display = 'block';
  $('results').scrollIntoView({behavior:'smooth', block:'start'});
}

renderItems();
</script>
</body>
</html>
"""


# ----------------------------------------------------------------------
#  SERVER
# ----------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        if self.path != "/solve":
            return self._send(404, b"Not found", "text/plain")
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            out = solve(payload)
            self._send(200, json.dumps(out).encode(), "application/json")
        except (ValueError, KeyError, TypeError) as e:
            msg = str(e) if isinstance(e, ValueError) else "Invalid input."
            self._send(400, json.dumps({"error": msg}).encode(), "application/json")

    def log_message(self, *args):
        pass


def main():
    port = PORT
    while True:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    url = f"http://localhost:{port}"
    print(f"KnapsackLab running at {url}   (press Ctrl+C to stop)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
