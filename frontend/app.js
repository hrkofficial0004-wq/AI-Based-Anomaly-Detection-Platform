/**
 * HealthAI Monitor – Dashboard JavaScript
 * Handles: SocketIO real-time updates, Chart.js charts,
 *          KPI polling, anomaly table, vitals form submission.
 */

const API = 'http://localhost:5000';
const MAX_CHART_POINTS = 40;

// ─── State ───────────────────────────────────────────────────────────────────
const state = {
  connected: false,
  hrData:    [],
  spo2Data:  [],
  bpSysData: [],
  bpDiaData: [],
  labels:    [],
};

// ─── Clock ───────────────────────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById('liveClock');
  const tick = () => {
    el.textContent = new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
    });
  };
  tick();
  setInterval(tick, 1000);
}

// ─── ChartJS helpers ─────────────────────────────────────────────────────────
function makeGradient(ctx, colorTop, colorBot) {
  const g = ctx.createLinearGradient(0, 0, 0, 180);
  g.addColorStop(0, colorTop);
  g.addColorStop(1, colorBot);
  return g;
}

function buildLineChart(canvasId, label, color, fillColor) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label,
        data: [],
        borderColor: color,
        backgroundColor: fillColor,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.4,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 2.5,
      animation: { duration: 300 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(10,18,36,0.95)',
          borderColor: 'rgba(99,179,244,0.3)',
          borderWidth: 1,
          titleColor: '#e8f0fe',
          bodyColor: '#8fa3c7',
          padding: 10,
        }
      },
      scales: {
        x: {
          display: true,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#4a5c7a', maxTicksLimit: 6, font: { size: 10 } },
        },
        y: {
          display: true,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#4a5c7a', font: { size: 10 } },
        }
      }
    }
  });
}

// ─── Charts ──────────────────────────────────────────────────────────────────
const hrChart = buildLineChart('hrChart', 'Heart Rate', '#f87171', 'rgba(248,113,113,0.1)');
const spo2Chart = buildLineChart('spo2Chart', 'SpO₂', '#34d399', 'rgba(52,211,153,0.1)');
const bpChart = (() => {
  const canvas = document.getElementById('bpChart');
  const ctx = canvas.getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Systolic',
          data: [],
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245,158,11,0.08)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.4,
          fill: true,
        },
        {
          label: 'Diastolic',
          data: [],
          borderColor: '#a78bfa',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.4,
          borderDash: [4, 3],
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 2.5,
      animation: { duration: 300 },
      plugins: {
        legend: {
          display: true,
          labels: { color: '#8fa3c7', font: { size: 10 }, boxWidth: 14, padding: 10 }
        },
        tooltip: {
          backgroundColor: 'rgba(10,18,36,0.95)',
          borderColor: 'rgba(99,179,244,0.3)',
          borderWidth: 1,
          titleColor: '#e8f0fe',
          bodyColor: '#8fa3c7',
          padding: 10,
        }
      },
      scales: {
        x: { display: true, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#4a5c7a', maxTicksLimit: 6, font: { size: 10 } } },
        y: { display: true, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#4a5c7a', font: { size: 10 } } }
      }
    }
  });
})();

function pushChartPoint(vital) {
  const ts = new Date(vital.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  [hrChart, spo2Chart, bpChart].forEach(c => {
    if (c.data.labels.length >= MAX_CHART_POINTS) c.data.labels.shift();
    c.data.labels.push(ts);
  });

  if (hrChart.data.datasets[0].data.length >= MAX_CHART_POINTS) hrChart.data.datasets[0].data.shift();
  hrChart.data.datasets[0].data.push(vital.heart_rate);
  hrChart.update('none');

  if (spo2Chart.data.datasets[0].data.length >= MAX_CHART_POINTS) spo2Chart.data.datasets[0].data.shift();
  spo2Chart.data.datasets[0].data.push(vital.spo2);
  spo2Chart.update('none');

  [0, 1].forEach(i => {
    if (bpChart.data.datasets[i].data.length >= MAX_CHART_POINTS) bpChart.data.datasets[i].data.shift();
  });
  bpChart.data.datasets[0].data.push(vital.systolic_bp);
  bpChart.data.datasets[1].data.push(vital.diastolic_bp);
  bpChart.update('none');
}

// ─── KPI ─────────────────────────────────────────────────────────────────────
async function refreshStats() {
  try {
    const res = await fetch(`${API}/api/stats`);
    if (!res.ok) return;
    const data = await res.json();
    animCount('totalVitals',    data.total_vitals);
    animCount('totalAnomalies', data.total_anomalies);
    animCount('criticalCount',  data.by_severity?.CRITICAL ?? 0);
    animCount('highCount',      data.by_severity?.HIGH ?? 0);
    document.getElementById('anomalyRate').textContent = `${data.anomaly_rate}% anomaly rate`;
  } catch (_) {}
}

function animCount(id, target) {
  const el = document.getElementById(id);
  const current = parseInt(el.textContent) || 0;
  if (current === target) return;
  const step = Math.ceil(Math.abs(target - current) / 12);
  let val = current;
  const iv = setInterval(() => {
    val = val < target ? Math.min(val + step, target) : Math.max(val - step, target);
    el.textContent = val.toLocaleString();
    if (val === target) clearInterval(iv);
  }, 40);
}

// ─── Severity helpers ─────────────────────────────────────────────────────────
const SEV_ICONS = { CRITICAL: '🚨', HIGH: '🔴', MEDIUM: '🟡', LOW: '🟢' };

function sevBadge(sev) {
  return `<span class="sev-badge sev-${sev}">${SEV_ICONS[sev] || ''} ${sev}</span>`;
}

function scoreBar(score) {
  const pct = Math.round(score * 100);
  let color = '#2ed573';
  if (score >= 0.65) color = '#ff4757';
  else if (score >= 0.45) color = '#ff6b35';
  else if (score >= 0.25) color = '#ffd32a';
  return `<div class="score-bar">
    <span>${pct}%</span>
    <div class="score-track"><div class="score-fill" style="width:${pct}%;background:${color}"></div></div>
  </div>`;
}

// ─── Anomaly Table ────────────────────────────────────────────────────────────
async function loadAnomalies() {
  const severity = document.getElementById('severityFilter').value;
  const url = `${API}/api/anomalies?only_anomalies=true&limit=100${severity ? '&severity=' + severity : ''}`;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rows = await res.json();
    renderTable(rows);
  } catch (e) {
    document.getElementById('anomalyTbody').innerHTML =
      `<tr><td colspan="10" style="text-align:center;color:#ff4757;padding:30px">⚠️ Could not load anomalies – backend offline?</td></tr>`;
  }
}

function renderTable(rows) {
  const tbody = document.getElementById('anomalyTbody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;color:#4a5c7a;padding:30px">No anomalies yet – waiting for data…</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r, i) => {
    const ts = new Date(r.timestamp).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'medium' });
    return `<tr class="${i === 0 ? 'new-row' : ''}">
      <td>${r.patient_id ?? '–'}</td>
      <td>${r.heart_rate ?? '–'} <small style="color:#4a5c7a">bpm</small></td>
      <td>${r.spo2 ?? '–'}<small style="color:#4a5c7a">%</small></td>
      <td>${r.systolic_bp ?? '–'}/${r.diastolic_bp ?? '–'}</td>
      <td>${r.temperature ?? '–'}<small style="color:#4a5c7a">°C</small></td>
      <td>${scoreBar(r.anomaly_score)}</td>
      <td>${sevBadge(r.severity)}</td>
      <td style="max-width:220px;white-space:normal;color:#8fa3c7;font-size:0.78rem">${r.notes || '–'}</td>
      <td style="color:#4a5c7a">${ts}</td>
      <td><button class="btn-alert" id="alert-${r.id}" onclick="triggerAlert(${r.id})"${r.alerted ? ' disabled' : ''}>${r.alerted ? '✓ Sent' : '📧 Alert'}</button></td>
    </tr>`;
  }).join('');
}

async function triggerAlert(id) {
  const btn = document.getElementById(`alert-${id}`);
  if (!btn || btn.disabled) return;
  btn.disabled = true;
  btn.textContent = '…';
  try {
    await fetch(`${API}/api/anomalies/${id}/alert`, { method: 'POST' });
    btn.textContent = '✓ Sent';
    showToast('Alert Sent', `Alert triggered for anomaly #${id}`, 'HIGH');
  } catch (_) {
    btn.disabled = false;
    btn.textContent = '📧 Alert';
  }
}
window.triggerAlert = triggerAlert;

// ─── Toasts ───────────────────────────────────────────────────────────────────
function showToast(title, msg, severity = 'HIGH', duration = 5000) {
  const container = document.getElementById('toastContainer');
  const icon = SEV_ICONS[severity] || '⚠️';
  const toast = document.createElement('div');
  toast.className = `toast ${severity}`;
  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${msg}</div>
    </div>
    <span class="toast-close" onclick="this.closest('.toast').remove()">✕</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

// ─── Socket.IO ────────────────────────────────────────────────────────────────
function connectSocket() {
  const statusBadge = document.getElementById('connectionStatus');
  const statusText  = document.getElementById('statusText');

  const socket = io(API, { transports: ['polling'], reconnectionAttempts: 20 });

  socket.on('connect', () => {
    state.connected = true;
    statusBadge.classList.add('connected');
    statusText.textContent = 'Live Feed Active';
    refreshStats();
    loadAnomalies();
  });

  socket.on('disconnect', () => {
    state.connected = false;
    statusBadge.classList.remove('connected');
    statusText.textContent = 'Reconnecting…';
  });

  socket.on('vital_update', (vital) => {
    pushChartPoint(vital);
  });

  socket.on('new_anomaly', (data) => {
    refreshStats();
    // Prepend row to table
    const tbody = document.getElementById('anomalyTbody');
    const ts = new Date(data.timestamp).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'medium' });
    const tempId = `live-${Date.now()}`;
    const newRow = document.createElement('tr');
    newRow.className = 'new-row';
    newRow.innerHTML = `
      <td>${data.patient_id}</td>
      <td>${data.heart_rate} <small style="color:#4a5c7a">bpm</small></td>
      <td>${data.spo2}<small style="color:#4a5c7a">%</small></td>
      <td>${data.systolic_bp}/${data.diastolic_bp}</td>
      <td>${data.temperature}<small style="color:#4a5c7a">°C</small></td>
      <td>${scoreBar(data.anomaly_score)}</td>
      <td>${sevBadge(data.severity)}</td>
      <td style="max-width:220px;white-space:normal;color:#8fa3c7;font-size:0.78rem">${data.notes || '–'}</td>
      <td style="color:#4a5c7a">${ts}</td>
      <td><button class="btn-alert" id="${tempId}" onclick="triggerAlert(0)">📧 Alert</button></td>`;

    // Remove "no data" placeholder if present
    const placeholder = tbody.querySelector('.loading-row, [colspan="10"]');
    if (placeholder) placeholder.closest('tr')?.remove();

    tbody.insertBefore(newRow, tbody.firstChild);

    // Keep table capped at 100 rows
    while (tbody.rows.length > 100) tbody.deleteRow(tbody.rows.length - 1);

    if (data.severity === 'CRITICAL' || data.severity === 'HIGH') {
      showToast(
        `${data.severity} Anomaly – Patient ${data.patient_id}`,
        data.notes || 'Abnormal vital signs detected',
        data.severity,
        data.severity === 'CRITICAL' ? 8000 : 5000
      );
    }
  });
}

// ─── Manual form ─────────────────────────────────────────────────────────────
document.getElementById('injectForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.textContent = 'Analysing…';

  const body = {
    patient_id:   document.getElementById('inp_pid').value,
    heart_rate:   parseFloat(document.getElementById('inp_hr').value),
    spo2:         parseFloat(document.getElementById('inp_spo2').value),
    systolic_bp:  parseFloat(document.getElementById('inp_sys').value),
    diastolic_bp: parseFloat(document.getElementById('inp_dia').value),
    temperature:  parseFloat(document.getElementById('inp_temp').value),
  };

  const result = document.getElementById('injectResult');
  result.className = 'inject-result';

  try {
    const res = await fetch(`${API}/api/vitals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Submission failed');

    const sev = data.severity;
    result.classList.add(sev === 'CRITICAL' || sev === 'HIGH' ? 'warning' : 'success');
    result.innerHTML = `
      <strong>Analysis Complete</strong> – Patient ${body.patient_id}<br>
      Severity: ${sevBadge(sev)} &nbsp; Score: <strong>${Math.round(data.anomaly_score * 100)}%</strong><br>
      <span style="color:#8fa3c7;font-size:0.8rem">${data.notes}</span>`;
    refreshStats();
    loadAnomalies();
    if (sev === 'CRITICAL' || sev === 'HIGH') showToast(`${sev} – Patient ${body.patient_id}`, data.notes, sev);
  } catch (err) {
    result.classList.add('error');
    result.innerHTML = `<strong>Error:</strong> ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analyse Vitals';
  }
});

// Inject anomaly button – pre-fill with dangerous values
document.getElementById('injectAnomalyBtn').addEventListener('click', () => {
  document.getElementById('inp_pid').value   = `P00${Math.ceil(Math.random() * 5)}`;
  document.getElementById('inp_hr').value    = (150 + Math.floor(Math.random() * 50)).toString();
  document.getElementById('inp_spo2').value  = (70 + Math.floor(Math.random() * 10)).toString();
  document.getElementById('inp_sys').value   = (160 + Math.floor(Math.random() * 40)).toString();
  document.getElementById('inp_dia').value   = (100 + Math.floor(Math.random() * 20)).toString();
  document.getElementById('inp_temp').value  = (39.5 + Math.random()).toFixed(1);
  document.getElementById('injectForm').requestSubmit();
});

// Refresh/filter controls
document.getElementById('refreshBtn').addEventListener('click', loadAnomalies);
document.getElementById('severityFilter').addEventListener('change', loadAnomalies);

// ─── Polling fallback ─────────────────────────────────────────────────────────
setInterval(refreshStats, 10000);
setInterval(loadAnomalies, 15000);

// ─── Bootstrap ────────────────────────────────────────────────────────────────
startClock();
connectSocket();
