/**
 * APEN Agent MVP – Frontend
 * All API base URL is same origin (relative).
 */

const API = '';

function setResult(el, content, type = '') {
  if (!el) return;
  el.textContent = content;
  el.className = 'result-box' + (type ? ' ' + type : '');
  el.style.display = content ? 'block' : 'none';
}

function setLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? '…' : btn.dataset.label || 'Envoyer';
}

async function checkHealth() {
  const statusEl = document.getElementById('apiStatus');
  try {
    const r = await fetch(API + '/health');
    statusEl.textContent = r.ok ? 'API OK' : 'API erreur';
    statusEl.className = 'api-status ' + (r.ok ? 'ok' : 'err');
  } catch (e) {
    statusEl.textContent = 'API hors ligne';
    statusEl.className = 'api-status err';
  }
}

// --- Intent ---
document.getElementById('intentBtn')?.addEventListener('click', async () => {
  const msg = document.getElementById('intentMessage').value.trim();
  const lang = document.getElementById('intentLang').value;
  const resultEl = document.getElementById('intentResult');
  const btn = document.getElementById('intentBtn');
  if (!msg) {
    setResult(resultEl, 'Saisissez un message.', 'error');
    return;
  }
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, '');
  try {
    const r = await fetch(API + '/intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, language: lang }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    // Same shape as audio: intent, action, routing_target
    const text = [
      'Intent: ' + data.intent,
      'Action: ' + data.action,
      'Routage: ' + (data.routing_target || 'reception'),
    ].join('\n');
    setResult(resultEl, text, 'success');
  } catch (e) {
    setResult(resultEl, 'Erreur: ' + e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Audio: show selected file name for demo ---
document.getElementById('audioFile')?.addEventListener('change', function () {
  const nameEl = document.getElementById('audioFileName');
  if (!nameEl) return;
  const file = this.files?.[0];
  nameEl.textContent = file ? 'Fichier : ' + file.name : '';
});

// --- Audio ---
document.getElementById('audioBtn')?.addEventListener('click', async () => {
  const fileInput = document.getElementById('audioFile');
  const lang = document.getElementById('audioLang').value;
  const resultEl = document.getElementById('audioResult');
  const btn = document.getElementById('audioBtn');
  const file = fileInput?.files?.[0];
  if (!file) {
    setResult(resultEl, 'Choisissez un fichier audio.', 'error');
    return;
  }
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, 'Transcription en cours…');
  try {
    const form = new FormData();
    form.append('file', file);
    const r = await fetch(API + '/audio/intent?language=' + encodeURIComponent(lang), {
      method: 'POST',
      body: form,
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    const text = [
      'Transcription: ' + (data.transcript || '(vide)'),
      'Intent: ' + data.intent,
      'Action: ' + data.action,
      'Routage: ' + data.routing_target,
    ].join('\n');
    setResult(resultEl, text, 'success');
  } catch (e) {
    setResult(resultEl, 'Erreur: ' + e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Slots ---
document.getElementById('slotsBtn')?.addEventListener('click', async () => {
  const dateInput = document.getElementById('slotsDate');
  const date = dateInput?.value || new Date().toISOString().slice(0, 10);
  const resultEl = document.getElementById('slotsResult');
  const btn = document.getElementById('slotsBtn');
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, 'Chargement…');
  try {
    const r = await fetch(API + '/slots?date=' + encodeURIComponent(date));
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    const lines = (data.slots || []).slice(0, 10).map(s => s.start + ' → ' + s.end);
    setResult(resultEl, lines.length ? lines.join('\n') : 'Aucun créneau.', 'success');
  } catch (e) {
    setResult(resultEl, 'Erreur: ' + e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Create appointment ---
document.getElementById('apptBtn')?.addEventListener('click', async () => {
  const start = document.getElementById('apptStart').value;
  const end = document.getElementById('apptEnd').value;
  const summary = document.getElementById('apptSummary').value.trim();
  const email = document.getElementById('apptEmail').value.trim() || null;
  const resultEl = document.getElementById('apptResult');
  const btn = document.getElementById('apptBtn');
  if (!start || !end || !summary) {
    setResult(resultEl, 'Remplissez début, fin et objet.', 'error');
    return;
  }
  const startIso = new Date(start).toISOString();
  const endIso = new Date(end).toISOString();
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, '');
  try {
    const r = await fetch(API + '/appointments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_iso: startIso,
        end_iso: endIso,
        summary,
        description: 'APEN – Récupération tenue / agent MVP',
        attendee_email: email,
      }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    setResult(resultEl, 'RDV créé: ' + (data.htmlLink || data.id || JSON.stringify(data)), 'success');
  } catch (e) {
    setResult(resultEl, 'Erreur: ' + e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Summaries: refresh list ---
function renderSummaries(list) {
  const container = document.getElementById('summariesList');
  if (!container) return;
  if (!list || list.length === 0) {
    container.innerHTML = '<p class="card-desc">Aucune synthèse.</p>';
    return;
  }
  container.innerHTML = list
    .map(
      (s) => `
    <div class="summary-item" data-id="${s.id}">
      <div class="info">
        <span class="name">${escapeHtml(s.caller_name)}</span> · ${escapeHtml(s.caller_phone)}
        <div class="meta">${escapeHtml(s.reason)} · ${s.site} · ${s.urgency} · ${s.status}</div>
      </div>
      <div class="actions">
        ${s.status === 'pending' ? `<button type="button" class="btn btn-sm btn-secondary" data-action="called">Rappelé</button>` : ''}
        <button type="button" class="btn btn-sm btn-secondary" data-action="closed">Clôturer</button>
      </div>
    </div>
  `
    )
    .join('');

  container.querySelectorAll('[data-action]').forEach((b) => {
    b.addEventListener('click', async () => {
      const item = b.closest('.summary-item');
      const id = item?.dataset?.id;
      const status = b.dataset.action;
      if (!id || !status) return;
      try {
        const r = await fetch(API + '/summaries/' + id, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status }),
        });
        if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
        loadSummaries();
      } catch (e) {
        alert('Erreur: ' + e.message);
      }
    });
  });
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

async function loadSummaries() {
  const filter = document.getElementById('summariesFilter')?.value || '';
  try {
    const r = await fetch(API + '/summaries' + (filter ? '?status=' + filter : ''));
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    renderSummaries(data.summaries || []);
  } catch (e) {
    document.getElementById('summariesList').innerHTML =
      '<p class="result-box error">Erreur: ' + escapeHtml(e.message) + '</p>';
  }
}

document.getElementById('summariesRefresh')?.addEventListener('click', loadSummaries);
document.getElementById('summariesFilter')?.addEventListener('change', loadSummaries);

// --- Add summary ---
document.getElementById('sumAddBtn')?.addEventListener('click', async () => {
  const name = document.getElementById('sumName').value.trim();
  const phone = document.getElementById('sumPhone').value.trim();
  const reason = document.getElementById('sumReason').value.trim();
  const site = document.getElementById('sumSite').value;
  const urgency = document.getElementById('sumUrgency').value;
  const resultEl = document.getElementById('sumAddResult');
  const btn = document.getElementById('sumAddBtn');
  if (!name || !phone || !reason) {
    setResult(resultEl, 'Nom, téléphone et motif requis.', 'error');
    return;
  }
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, '');
  try {
    const r = await fetch(API + '/summaries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        caller_name: name,
        caller_phone: phone,
        reason,
        site,
        urgency,
      }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    setResult(resultEl, 'Enregistré. ID: ' + data.id, 'success');
    document.getElementById('sumName').value = '';
    document.getElementById('sumPhone').value = '';
    document.getElementById('sumReason').value = '';
    loadSummaries();
  } catch (e) {
    setResult(resultEl, 'Erreur: ' + e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Voice webhook URL (from /config or current origin)
const webhookEl = document.getElementById('voiceWebhookUrl');
if (webhookEl) {
  fetch(API + '/config')
    .then((r) => r.ok ? r.json() : {})
    .then((c) => {
      webhookEl.textContent = (c.webhook_url || window.location.origin + '/webhooks/vapi');
    })
    .catch(() => {
      webhookEl.textContent = window.location.origin + '/webhooks/vapi';
    });
}
document.getElementById('voiceCopyBtn')?.addEventListener('click', () => {
  const url = document.getElementById('voiceWebhookUrl')?.textContent;
  if (url && navigator.clipboard) navigator.clipboard.writeText(url).then(() => { alert('URL copiée.'); });
});

// Init: health + load summaries + set default date
checkHealth();
loadSummaries();
const today = new Date().toISOString().slice(0, 10);
const dateEl = document.getElementById('slotsDate');
if (dateEl && !dateEl.value) dateEl.value = today;
setInterval(checkHealth, 30000);
