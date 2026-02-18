/**
 * APEN Agent MVP – Frontend
 * Language selector drives intent/audio language; flow shows next-step and auto-scrolls.
 */

const API = '';
const LANG_KEY = 'apen-lang';

function setResult(el, content, type = '') {
  if (!el) return;
  el.textContent = content;
  el.className = 'result-box' + (type ? ' ' + type : '');
  el.style.display = content ? 'block' : 'none';
}

function setNextStep(el, content) {
  if (!el) return;
  el.textContent = content || '';
  el.style.display = content ? 'block' : 'none';
}

function setLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? '…' : btn.dataset.label || 'Submit';
}

function getLang() {
  return localStorage.getItem(LANG_KEY) || 'en';
}

function setLang(lang) {
  localStorage.setItem(LANG_KEY, lang);
  const select = document.getElementById('langSelect');
  const intentLang = document.getElementById('intentLang');
  const audioLang = document.getElementById('audioLang');
  if (select) select.value = lang;
  if (intentLang) intentLang.value = lang;
  if (audioLang) audioLang.value = lang;
}

function applyFlowAfterIntent(data, nextStepElId, scrollTargetId) {
  const action = (data && data.action) || '';
  const routing = (data && data.routing_target) || '';
  const nextEl = document.getElementById(nextStepElId);
  const scrollEl = scrollTargetId ? document.getElementById(scrollTargetId) : null;

  if (!nextEl) return;
  setNextStep(nextEl, '');

  if (action === 'book_appointment' && routing === 'in_agent') {
    setNextStep(nextEl, '→ Offer slots in the « Available slots » section below.');
    if (scrollEl) scrollEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else if (action === 'provide_info' && routing === 'in_agent') {
    setNextStep(nextEl, '→ Give the requested info (hours, address) or save a callback in « Callbacks ».');
  } else if (action === 'collect_summary' || routing === 'reception') {
    setNextStep(nextEl, '→ Callback summary: see the « Callbacks » section below.');
    if (document.getElementById('summaries')) document.getElementById('summaries').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

async function checkHealth() {
  const statusEl = document.getElementById('apiStatus');
  if (!statusEl) return;
  try {
    const r = await fetch(API + '/health');
    statusEl.textContent = r.ok ? 'API OK' : 'API error';
    statusEl.className = 'api-status ' + (r.ok ? 'ok' : 'err');
  } catch (e) {
    statusEl.textContent = 'API offline';
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
    setResult(resultEl, 'Enter a message.', 'error');
    return;
  }
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, '');
  setNextStep(document.getElementById('intentNextStep'), '');
  try {
    const r = await fetch(API + '/intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, language: lang }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    const text = [
      'Intent: ' + data.intent,
      'Action: ' + data.action,
      'Routing: ' + (data.routing_target || 'reception'),
    ].join('\n');
    setResult(resultEl, text, 'success');
    applyFlowAfterIntent(data, 'intentNextStep', 'slots');
  } catch (e) {
    setResult(resultEl, 'Error: ' + (e.message || 'network'), 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Audio: show selected file name for demo ---
document.getElementById('audioFile')?.addEventListener('change', function () {
  const nameEl = document.getElementById('audioFileName');
  if (!nameEl) return;
  const file = this.files?.[0];
  nameEl.textContent = file ? 'File: ' + file.name : '';
});

// --- Audio ---
document.getElementById('audioBtn')?.addEventListener('click', async () => {
  const fileInput = document.getElementById('audioFile');
  const lang = document.getElementById('audioLang').value;
  const resultEl = document.getElementById('audioResult');
  const btn = document.getElementById('audioBtn');
  const file = fileInput?.files?.[0];
  if (!file) {
    setResult(resultEl, 'Choose an audio file.', 'error');
    return;
  }
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, 'Transcribing…');
  setNextStep(document.getElementById('audioNextStep'), '');
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
      'Transcription: ' + (data.transcript || '(empty)'),
      'Intent: ' + data.intent,
      'Action: ' + data.action,
      'Routing: ' + data.routing_target,
    ].join('\n');
    setResult(resultEl, text, 'success');
    applyFlowAfterIntent(data, 'audioNextStep', 'slots');
  } catch (e) {
    setResult(resultEl, 'Error: ' + (e.message || 'network'), 'error');
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
  setResult(resultEl, 'Loading…');
  try {
    const r = await fetch(API + '/slots?date=' + encodeURIComponent(date));
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    const lines = (data.slots || []).slice(0, 10).map(s => s.start + ' → ' + s.end);
    setResult(resultEl, lines.length ? lines.join('\n') : 'No slots.', 'success');
  } catch (e) {
    setResult(resultEl, 'Error: ' + (e.message || 'network'), 'error');
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
    setResult(resultEl, 'Fill in start, end and subject.', 'error');
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
        description: 'APEN – Uniform collection / agent MVP',
        attendee_email: email,
      }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    setResult(resultEl, 'Appointment created: ' + (data.htmlLink || data.id || JSON.stringify(data)), 'success');
  } catch (e) {
    setResult(resultEl, 'Error: ' + (e.message || 'network'), 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Summaries: refresh list ---
function renderSummaries(list) {
  const container = document.getElementById('summariesList');
  if (!container) return;
  if (!list || list.length === 0) {
    container.innerHTML = '<p class="card-desc">No summaries.</p>';
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
        ${s.status === 'pending' ? `<button type="button" class="btn btn-sm btn-secondary" data-action="called">Called back</button>` : ''}
        <button type="button" class="btn btn-sm btn-secondary" data-action="closed">Close</button>
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
        alert('Error: ' + e.message);
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
      '<p class="result-box error">Error: ' + escapeHtml(e.message) + '</p>';
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
    setResult(resultEl, 'Name, phone and reason required.', 'error');
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
    setResult(resultEl, 'Saved. ID: ' + data.id, 'success');
    document.getElementById('sumName').value = '';
    document.getElementById('sumPhone').value = '';
    document.getElementById('sumReason').value = '';
    loadSummaries();
  } catch (e) {
    setResult(resultEl, 'Error: ' + (e.message || 'network'), 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Test call taking (simulate POST /voice/process) ---
document.getElementById('testCallBtn')?.addEventListener('click', async () => {
  const transcriptEl = document.getElementById('callTranscript');
  const phoneEl = document.getElementById('callPhone');
  const resultEl = document.getElementById('testCallResult');
  const nextEl = document.getElementById('testCallNextStep');
  const btn = document.getElementById('testCallBtn');
  const transcript = (transcriptEl?.value || '').trim();
  if (!transcript) {
    setResult(resultEl, 'Enter what the caller said.', 'error');
    return;
  }
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, '');
  setNextStep(nextEl, '');
  try {
    const r = await fetch(API + '/voice/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript,
        caller_phone: (phoneEl?.value || '').trim(),
        language: getLang(),
      }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);

    const lines = [
      'Intent: ' + (data.intent || '—'),
      'Action: ' + (data.action || '—'),
      'Routing: ' + (data.routing_target || '—'),
      'Response: ' + (data.response_type || '—'),
    ];
    if (data.transfer_number) {
      lines.push('Transfer number: ' + data.transfer_number);
      lines.push('Message: « ' + (data.say_message || '') + ' »');
    } else {
      lines.push('Message to say: « ' + (data.say_message || '') + ' »');
      if (data.response_type === 'callback') {
        lines.push('');
        lines.push('→ Callback summary created (see Callbacks section).');
        if (typeof loadSummaries === 'function') loadSummaries();
      }
    }
    setResult(resultEl, lines.join('\n'), 'success');
    if (data.response_type === 'callback') {
      setNextStep(nextEl, 'A summary was saved. Refresh the Callbacks section to see it.');
    }
  } catch (e) {
    setResult(resultEl, 'Error: ' + (e.message || 'network'), 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Voice webhook URL (from /config or current origin)
const webhookEl = document.getElementById('voiceWebhookUrl');
if (webhookEl) {
  const url = window.location.origin + '/webhooks/vapi';
  webhookEl.value = url;
  fetch(API + '/config')
    .then((r) => r.ok ? r.json() : {})
    .then((c) => {
      webhookEl.value = (c.webhook_url || url);
    })
    .catch(() => {
      webhookEl.value = url;
    });
}
document.getElementById('voiceCopyBtn')?.addEventListener('click', () => {
  const input = document.getElementById('voiceWebhookUrl');
  const url = input?.value || input?.textContent;
  if (url && navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => { alert('URL copied.'); });
  }
});

// --- Language selector (drives intent/audio; default FR, persisted)
setLang(getLang());
document.getElementById('langSelect')?.addEventListener('change', function () {
  setLang(this.value);
});
document.getElementById('intentLang')?.addEventListener('change', function () {
  localStorage.setItem(LANG_KEY, this.value);
  const langSelect = document.getElementById('langSelect');
  if (langSelect) langSelect.value = this.value;
  const audioLang = document.getElementById('audioLang');
  if (audioLang) audioLang.value = this.value;
});
document.getElementById('audioLang')?.addEventListener('change', function () {
  localStorage.setItem(LANG_KEY, this.value);
  const langSelect = document.getElementById('langSelect');
  if (langSelect) langSelect.value = this.value;
  const intentLang = document.getElementById('intentLang');
  if (intentLang) intentLang.value = this.value;
});

// Init: health + load summaries + set default date
checkHealth();
loadSummaries();
const today = new Date().toISOString().slice(0, 10);
const dateEl = document.getElementById('slotsDate');
if (dateEl && !dateEl.value) dateEl.value = today;
setInterval(checkHealth, 30000);
