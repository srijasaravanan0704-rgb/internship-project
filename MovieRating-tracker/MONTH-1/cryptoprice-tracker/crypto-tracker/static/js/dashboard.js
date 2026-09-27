const state = {
  coins: [],
  sortBy: "rank",
  order: "asc",
  filter: "all",
  query: "",
  watchlist: JSON.parse(localStorage.getItem("watchlist") || "[]"),
  alerts: JSON.parse(localStorage.getItem("alerts") || "[]"),
  focusSymbol: "BTC",
};

const BADGE_COLORS = ["#7C83FD", "#F0B44C", "#34D399", "#FB6C6C", "#5EC8D8", "#C58CF0"];

function fmtPrice(n) {
  if (n == null) return "—";
  if (n < 1) return "$" + n.toFixed(4);
  return "$" + n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
function fmtBig(n) {
  if (n == null) return "—";
  if (n >= 1e12) return "$" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e9) return "$" + (n / 1e9).toFixed(2) + "B";
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(2) + "M";
  return "$" + n.toFixed(0);
}
function fmtPct(n) {
  if (n == null) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}
function pctClass(n) { return n == null ? "" : n >= 0 ? "up" : "down"; }
function badgeColor(symbol) {
  let hash = 0;
  for (const ch of symbol) hash = ch.charCodeAt(0) + ((hash << 5) - hash);
  return BADGE_COLORS[Math.abs(hash) % BADGE_COLORS.length];
}
function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("is-visible");
  setTimeout(() => t.classList.remove("is-visible"), 2200);
}

async function fetchCoins() {
  const params = new URLSearchParams({ sort: state.sortBy, order: state.order, q: state.query });
  const res = await fetch(`/api/coins?${params}`);
  const data = await res.json();
  state.coins = data.coins || [];
  updateHeader(data);
  renderTable();
  renderFocusChart();
  populateAlertSymbols();
  checkAlerts();
}

function updateHeader(data) {
  const updated = data.updated_at ? new Date(data.updated_at).toLocaleString() : "no data yet — run the scraper";
  document.getElementById("last-updated").textContent = `Last updated: ${updated}`;
  document.getElementById("stat-count").textContent = data.count ?? 0;

  const withChange = (data.coins || []).filter(c => c.change_24h != null);
  if (withChange.length) {
    const gainer = withChange.reduce((a, b) => (b.change_24h > a.change_24h ? b : a));
    const loser = withChange.reduce((a, b) => (b.change_24h < a.change_24h ? b : a));
    document.getElementById("stat-gainer").textContent = gainer.symbol;
    document.getElementById("stat-gainer-pct").textContent = fmtPct(gainer.change_24h);
    document.getElementById("stat-loser").textContent = loser.symbol;
    document.getElementById("stat-loser-pct").textContent = fmtPct(loser.change_24h);
  }

  const pulse = data.market_pulse ?? 50;
  document.getElementById("pulse-value").textContent = Math.round(pulse);
  const offset = 157 - (pulse / 100) * 157;
  const fill = document.getElementById("gauge-fill");
  fill.style.strokeDashoffset = offset;
  fill.style.stroke = pulse >= 55 ? "var(--up)" : pulse <= 45 ? "var(--down)" : "var(--brand)";
  document.getElementById("pulse-tag").textContent =
    pulse >= 55 ? "bullish tilt" : pulse <= 45 ? "bearish tilt" : "neutral / balanced";
}

function applyFilters(coins) {
  let out = coins;
  if (state.filter === "gainers") out = out.filter(c => (c.change_24h ?? 0) > 0);
  if (state.filter === "losers") out = out.filter(c => (c.change_24h ?? 0) < 0);
  if (state.filter === "watchlist") out = out.filter(c => state.watchlist.includes(c.symbol));
  return out;
}

function renderTable() {
  const tbody = document.getElementById("coin-table-body");
  const coins = applyFilters(state.coins);

  if (!state.coins.length) {
    tbody.innerHTML = `<tr><td colspan="10">
      <div class="empty-state">
        <strong>No data yet</strong>
        No scraped data was found. Run the scraper to populate the dashboard.
        <br><code>python scraper.py --headless</code>
      </div>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = coins.map(c => `
    <tr data-symbol="${c.symbol}">
      <td><button class="watch-star ${state.watchlist.includes(c.symbol) ? "is-active" : ""}" data-symbol="${c.symbol}">★</button></td>
      <td>${c.rank ?? "—"}</td>
      <td>
        <div class="coin-name-cell">
          <div class="coin-badge" style="background:${badgeColor(c.symbol)}">${c.symbol.slice(0, 1)}</div>
          <div>
            <div class="coin-name focus-trigger" data-symbol="${c.symbol}" style="cursor:pointer">${c.name}</div>
            <div class="coin-symbol">${c.symbol}</div>
          </div>
        </div>
      </td>
      <td>${fmtPrice(c.price)}</td>
      <td class="pct ${pctClass(c.change_1h)}">${fmtPct(c.change_1h)}</td>
      <td class="pct ${pctClass(c.change_24h)}">${fmtPct(c.change_24h)}</td>
      <td class="pct ${pctClass(c.change_7d)}">${fmtPct(c.change_7d)}</td>
      <td>${fmtBig(c.market_cap)}</td>
      <td>${fmtBig(c.volume_24h)}</td>
      <td><svg class="sparkline" viewBox="0 0 90 28" data-symbol="${c.symbol}"></svg></td>
    </tr>
  `).join("");

  document.querySelectorAll(".watch-star").forEach(btn =>
    btn.addEventListener("click", () => toggleWatchlist(btn.dataset.symbol)));
  document.querySelectorAll(".focus-trigger").forEach(el =>
    el.addEventListener("click", () => { state.focusSymbol = el.dataset.symbol; renderFocusChart(); }));

  coins.forEach(c => drawSparkline(c.symbol, c.change_7d));
}

function drawSparkline(symbol, trendHint) {
  const svg = document.querySelector(`svg.sparkline[data-symbol="${symbol}"]`);
  if (!svg) return;
  // Lightweight visual trend line seeded by the coin's own change values —
  // replaced with the real /api/coin/<symbol>/history series when available.
  fetch(`/api/coin/${symbol}/history`).then(r => r.json()).then(points => {
    let series = points.map(p => p.price);
    if (series.length < 2) {
      // fallback: synthesize a small trend so the row isn't empty
      const base = 10;
      series = Array.from({ length: 12 }, (_, i) => base + (trendHint || 0) * (i / 11) + Math.sin(i) * 0.6);
    }
    const min = Math.min(...series), max = Math.max(...series);
    const range = max - min || 1;
    const pts = series.map((v, i) => {
      const x = (i / (series.length - 1)) * 90;
      const y = 26 - ((v - min) / range) * 22;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    const color = series[series.length - 1] >= series[0] ? "var(--up)" : "var(--down)";
    svg.innerHTML = `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.8"/>`;
  });
}

function renderFocusChart() {
  const coin = state.coins.find(c => c.symbol === state.focusSymbol) || state.coins[0];
  if (!coin) return;
  state.focusSymbol = coin.symbol;
  document.getElementById("focus-coin-name").innerHTML = `${coin.name} <span class="muted">${coin.symbol}</span>`;
  document.getElementById("focus-price").textContent = fmtPrice(coin.price);

  fetch(`/api/coin/${coin.symbol}/history`).then(r => r.json()).then(points => {
    const svg = document.getElementById("focus-chart");
    let series = points.map(p => p.price);
    if (series.length < 2) series = [coin.price * 0.97, coin.price * 1.01, coin.price * 0.99, coin.price];
    const min = Math.min(...series), max = Math.max(...series);
    const range = max - min || 1;
    const w = 900, h = 220, pad = 10;
    const pts = series.map((v, i) => {
      const x = (i / (series.length - 1)) * (w - pad * 2) + pad;
      const y = h - pad - ((v - min) / range) * (h - pad * 2);
      return [x, y];
    });
    const linePath = "M" + pts.map(p => p.join(",")).join(" L");
    const areaPath = linePath + ` L${pts[pts.length - 1][0]},${h} L${pts[0][0]},${h} Z`;
    const up = series[series.length - 1] >= series[0];
    const color = up ? "#34D399" : "#FB6C6C";
    svg.innerHTML = `
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${color}" stop-opacity="0.28"/>
          <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <path d="${areaPath}" fill="url(#areaGrad)" stroke="none"/>
      <path d="${linePath}" fill="none" stroke="${color}" stroke-width="2.2"/>
    `;
  });
}

function toggleWatchlist(symbol) {
  const idx = state.watchlist.indexOf(symbol);
  if (idx >= 0) state.watchlist.splice(idx, 1);
  else state.watchlist.push(symbol);
  localStorage.setItem("watchlist", JSON.stringify(state.watchlist));
  renderTable();
}

/* ---------- Alerts ---------- */
function populateAlertSymbols() {
  const sel = document.getElementById("alert-symbol");
  if (!sel || sel.dataset.filled === "1") return;
  sel.innerHTML = state.coins.map(c => `<option value="${c.symbol}">${c.name} (${c.symbol})</option>`).join("");
  sel.dataset.filled = "1";
}

function renderAlertList() {
  const ul = document.getElementById("alert-list");
  ul.innerHTML = state.alerts.map((a, i) => `
    <li>
      <span>${a.symbol} ${a.direction === "above" ? "≥" : "≤"} $${a.price}</span>
      <button data-i="${i}">remove</button>
    </li>
  `).join("") || `<li class="muted small" style="justify-content:center">No alerts set</li>`;
  ul.querySelectorAll("button[data-i]").forEach(btn =>
    btn.addEventListener("click", () => {
      state.alerts.splice(Number(btn.dataset.i), 1);
      localStorage.setItem("alerts", JSON.stringify(state.alerts));
      renderAlertList();
    }));
}

function checkAlerts() {
  state.alerts.forEach(a => {
    const coin = state.coins.find(c => c.symbol === a.symbol);
    if (!coin || coin.price == null) return;
    const hit = a.direction === "above" ? coin.price >= a.price : coin.price <= a.price;
    if (hit) {
      const msg = `${coin.symbol} is now ${fmtPrice(coin.price)} (${a.direction} $${a.price})`;
      showToast(msg);
      if (Notification && Notification.permission === "granted") {
        new Notification("Price alert", { body: msg });
      }
    }
  });
}

/* ---------- Events ---------- */
document.getElementById("alert-form").addEventListener("submit", e => {
  e.preventDefault();
  const symbol = document.getElementById("alert-symbol").value;
  const direction = document.getElementById("alert-direction").value;
  const price = parseFloat(document.getElementById("alert-price").value);
  if (!symbol || !price) return;
  state.alerts.push({ symbol, direction, price });
  localStorage.setItem("alerts", JSON.stringify(state.alerts));
  document.getElementById("alert-price").value = "";
  renderAlertList();
  showToast(`Alert set for ${symbol}`);
});

document.querySelectorAll("th[data-sort]").forEach(th => th.addEventListener("click", () => {
  const key = th.dataset.sort;
  state.order = state.sortBy === key && state.order === "asc" ? "desc" : "asc";
  state.sortBy = key;
  fetchCoins();
}));

document.querySelectorAll(".chip").forEach(chip => chip.addEventListener("click", () => {
  document.querySelectorAll(".chip").forEach(c => c.classList.remove("is-active"));
  chip.classList.add("is-active");
  state.filter = chip.dataset.filter;
  renderTable();
}));

document.querySelectorAll(".range-tab").forEach(tab => tab.addEventListener("click", () => {
  document.querySelectorAll(".range-tab").forEach(t => t.classList.remove("is-active"));
  tab.classList.add("is-active");
}));

let searchTimer;
document.getElementById("search-input").addEventListener("input", e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { state.query = e.target.value; fetchCoins(); }, 250);
});

document.getElementById("refresh-btn").addEventListener("click", () => { fetchCoins(); showToast("Refreshed"); });

document.querySelectorAll(".nav-item").forEach(item => item.addEventListener("click", () => {
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("is-active"));
  item.classList.add("is-active");
  const view = item.dataset.view;
  document.getElementById("view-title").textContent = view[0].toUpperCase() + view.slice(1);
  if (view === "alerts") {
    document.getElementById("alerts-drawer").classList.add("is-open");
  } else if (view === "watchlist") {
    state.filter = "watchlist";
    document.querySelectorAll(".chip").forEach(c => c.classList.toggle("is-active", c.dataset.filter === "watchlist"));
    renderTable();
  }
}));

document.getElementById("close-alerts").addEventListener("click", () =>
  document.getElementById("alerts-drawer").classList.remove("is-open"));

if (window.Notification && Notification.permission === "default") {
  Notification.requestPermission();
}

/* ---------- Init ---------- */
renderAlertList();
fetchCoins();
setInterval(fetchCoins, 60000); // auto-refresh every 60s
