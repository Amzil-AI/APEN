/**
 * APEN Agent MVP – Frontend
 * Language selector drives intent/audio language; flow shows next-step and auto-scrolls.
 */

const API = '';
const LANG_KEY = 'apen-lang';
const UI_LANG_KEY = 'apen-ui-lang';

function getUILang() {
  return (window.APEN_I18N && window.APEN_I18N.getUILang) ? window.APEN_I18N.getUILang() : (localStorage.getItem(UI_LANG_KEY) || localStorage.getItem(LANG_KEY) || 'en').slice(0, 2);
}
function t(key) {
  return (window.APEN_I18N && window.APEN_I18N.t) ? window.APEN_I18N.t(key) : key;
}
function applyTranslations() {
  if (window.APEN_I18N && window.APEN_I18N.applyTranslations) window.APEN_I18N.applyTranslations();
}

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
  localStorage.setItem(UI_LANG_KEY, lang);
  const select = document.getElementById('langSelect');
  const intentLang = document.getElementById('intentLang');
  const audioLang = document.getElementById('audioLang');
  const callRecLang = document.getElementById('callRecordingLang');
  if (select) select.value = lang;
  if (intentLang) intentLang.value = lang;
  if (audioLang) audioLang.value = lang;
  if (callRecLang) callRecLang.value = lang;
  applyTranslations();
  if (typeof loadSummaries === 'function') loadSummaries();
  if (typeof loadCalls === 'function') loadCalls();
  if (typeof loadCalendarEvents === 'function') loadCalendarEvents();
}

function applyFlowAfterIntent(data, nextStepElId, scrollTargetId) {
  const action = (data && data.action) || '';
  const routing = (data && data.routing_target) || '';
  const nextEl = document.getElementById(nextStepElId);
  const scrollEl = scrollTargetId ? document.getElementById(scrollTargetId) : null;

  if (!nextEl) return;
  setNextStep(nextEl, '');

  if (action === 'book_appointment' && routing === 'in_agent') {
    setNextStep(nextEl, t('nextOfferSlots'));
    if (scrollEl) scrollEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else if (action === 'provide_info' && routing === 'in_agent') {
    setNextStep(nextEl, t('nextGiveInfo'));
  } else if (action === 'collect_summary' || routing === 'reception') {
    setNextStep(nextEl, t('nextCallback'));
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
    setResult(resultEl, t('enterMessage'), 'error');
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
    setResult(resultEl, t('chooseFile'), 'error');
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
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || data.message || r.statusText || (r.status === 503 ? 'Service unavailable. Set OPENAI_API_KEY on the server for voice transcription.' : 'Request failed'));
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
    setResult(resultEl, lines.length ? lines.join('\n') : t('noSlots'), 'success');
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
  const descEl = document.getElementById('apptDescription');
  const description = (descEl && descEl.value) ? descEl.value.trim() : 'APEN – Prise de rendez-vous (agent IA)';
  const email = document.getElementById('apptEmail').value.trim() || null;
  const resultEl = document.getElementById('apptResult');
  const btn = document.getElementById('apptBtn');
  if (!start || !end || !summary) {
    setResult(resultEl, t('fillStartEndSubject'), 'error');
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
        description,
        attendee_email: email,
      }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    setResult(resultEl, t('appointmentCreated') + ' ' + (data.htmlLink || data.id || JSON.stringify(data)), 'success');
    if (typeof loadCalendarEvents === 'function') loadCalendarEvents();
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
    container.innerHTML = '<p class="card-desc">' + escapeHtml(t('noSummaries')) + '</p>';
    return;
  }
  const transferTo = t('transferTo');
  const designated = t('designated');
  const addToCal = t('addToCalendarAi');
  const calledBack = t('calledBack');
  const closeBtn = t('close');
  container.innerHTML = list
    .map(
      (s) => {
        const d = s.designated_for_callback || {};
        const designatedLine = (d.label && d.number) ? `${transferTo}: ${escapeHtml(d.label)} — ${escapeHtml(d.number)}` : (d.label ? `${designated}: ${escapeHtml(d.label)}` : '');
        return `
    <div class="summary-item" data-id="${s.id}">
      <div class="info">
        <span class="name">${escapeHtml(s.caller_name)}</span> · ${escapeHtml(s.caller_phone)}
        <div class="meta">${escapeHtml(s.reason)} · ${s.site} · ${s.urgency} · ${s.status}</div>
        ${designatedLine ? `<div class="meta designated">${designatedLine}</div>` : ''}
      </div>
      <div class="actions">
        <button type="button" class="btn btn-sm btn-primary" data-action="add-to-calendar" data-i18n-title="addToCalendarAi">${escapeHtml(addToCal)}</button>
        ${s.status === 'pending' ? `<button type="button" class="btn btn-sm btn-secondary" data-action="called">${escapeHtml(calledBack)}</button>` : ''}
        <button type="button" class="btn btn-sm btn-secondary" data-action="closed">${escapeHtml(closeBtn)}</button>
      </div>
    </div>
  `;
      }
    )
    .join('');

  container.querySelectorAll('[data-action]').forEach((b) => {
    b.addEventListener('click', async () => {
      const item = b.closest('.summary-item');
      const id = item?.dataset?.id;
      const action = b.dataset.action;
      if (!id || !action) return;
      if (action === 'add-to-calendar') {
        try {
          setLoading(b, true);
          const r = await fetch(API + '/automation/callback-to-calendar/' + encodeURIComponent(id), { method: 'POST' });
          const data = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(data.detail || data.message || r.statusText);
          if (typeof loadCalendarEvents === 'function') loadCalendarEvents();
          alert(data.message || 'Event created: ' + (data.event?.id || ''));
        } catch (e) {
          alert('Error: ' + e.message);
        } finally {
          setLoading(b, false);
        }
        return;
      }
      try {
        const r = await fetch(API + '/summaries/' + id, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: action }),
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

// --- Calls (Vapi call log) ---
function renderCalls(list) {
  const container = document.getElementById('callsList');
  if (!container) return;
  if (!list || list.length === 0) {
    container.innerHTML = '<p class="card-desc">' + escapeHtml(t('noCalls')) + '</p>';
    return;
  }
  const dtLabel = t('dateTime');
  const callerLabel = t('caller');
  const transcriptLabel = t('transcript');
  const intentLabel = t('intent');
  const actionLabel = t('action');
  const outcomeLabel = t('outcome');
  const importanceLabel = t('importance');
  const schedulingLabel = t('scheduling');
  const callbackRef = t('callbackRef');
  const appointmentRef = t('appointmentRef');
  container.innerHTML = list
    .map(
      (c) => {
        const started = (c.started_at || '').replace('Z', ' ').slice(0, 19);
        const events = (c.events || []);
        const last = events[events.length - 1];
        const transcript = last ? (last.transcript || '—') : '—';
        const intent = last ? (last.intent || '—') : '—';
        const action = last ? (last.action || '—') : '—';
        const outcome = last ? (last.outcome || '—') : '—';
        const importance = c.importance != null ? String(c.importance) : '—';
        const scheduling = c.scheduling != null ? String(c.scheduling) : (c.appointment_id ? t('appointmentRef') : '—');
        const summaryId = c.summary_id || '';
        const appointmentId = c.appointment_id || '';
        const summaryReason = (c.summary_reason || '').slice(0, 150);
        const purpose = (c.purpose || '').trim() || '—';
        return `
    <div class="call-item">
      <p class="call-purpose" aria-label="Purpose">${escapeHtml(purpose)}</p>
      <dl class="call-fields">
        <dt>${escapeHtml(dtLabel)}</dt><dd>${escapeHtml(started)}</dd>
        <dt>${escapeHtml(callerLabel)}</dt><dd>${escapeHtml(c.caller_phone || '—')}</dd>
        <dt>${escapeHtml(transcriptLabel)}</dt><dd class="call-transcript">${escapeHtml(transcript)}</dd>
        <dt>${escapeHtml(intentLabel)}</dt><dd>${escapeHtml(intent)}</dd>
        <dt>${escapeHtml(actionLabel)}</dt><dd>${escapeHtml(action)}</dd>
        <dt>${escapeHtml(outcomeLabel)}</dt><dd>${escapeHtml(outcome)}</dd>
        <dt>${escapeHtml(importanceLabel)}</dt><dd>${escapeHtml(importance)}</dd>
        <dt>${escapeHtml(schedulingLabel)}</dt><dd>${escapeHtml(scheduling)}</dd>
        ${summaryReason ? `<dt>${escapeHtml(t('reason'))}</dt><dd class="call-reason">${escapeHtml(summaryReason)}${summaryReason.length >= 150 ? '…' : ''}</dd>` : ''}
      </dl>
      ${summaryId ? `<div class="call-ref">${escapeHtml(callbackRef)}: <code>${escapeHtml(summaryId)}</code></div>` : ''}
      ${appointmentId ? `<div class="call-ref">${escapeHtml(appointmentRef)}: <code>${escapeHtml(appointmentId)}</code></div>` : ''}
    </div>
  `;
      }
    )
    .join('');
}

async function loadCalls() {
  const container = document.getElementById('callsList');
  if (!container) return;
  try {
    const r = await fetch(API + '/calls');
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    renderCalls(data.calls || []);
  } catch (e) {
    container.innerHTML = '<p class="result-box error">Error: ' + escapeHtml(e.message) + '</p>';
  }
}

async function syncAndLoadCalls() {
  const btn = document.getElementById('callsRefresh');
  const status = document.getElementById('callsSyncStatus');
  const container = document.getElementById('callsList');
  if (!container) return;

  const fmt = (key, vars = {}) => {
    let out = t(key);
    Object.keys(vars).forEach((k) => {
      out = out.replace(`{${k}}`, String(vars[k]));
    });
    return out;
  };

  const setStatus = (kind, msg) => {
    if (!status) return;
    status.className = 'result-box' + (kind ? ' ' + kind : '');
    status.textContent = msg;
  };
  
  // Show syncing state
  const originalText = btn ? (btn.dataset.label || btn.textContent || '') : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = t('syncingVapi');
  }
  setStatus('', t('syncingVapi'));
  
  try {
    // First, try to sync from VAPI (optional if backend route exists)
    let syncStatus = null;
    try {
      const syncR = await fetch(API + '/vapi/sync');
      const syncText = await syncR.text();
      let syncData = null;
      try {
        syncData = syncText ? JSON.parse(syncText) : null;
      } catch (_) {
        syncData = null;
      }

      if (syncR.ok && syncData && Number(syncData.synced || 0) > 0) {
        syncStatus = {
          kind: 'success',
          text: fmt('syncDone', { count: Number(syncData.synced || 0) }),
        };
      } else if (syncR.ok) {
        syncStatus = {
          kind: '',
          text: t('syncNoNew'),
        };
      } else if (syncR.status === 404) {
        syncStatus = {
          kind: '',
          text: t('syncUnavailable'),
        };
      } else if (!syncR.ok && syncR.status !== 404) {
        syncStatus = {
          kind: 'error',
          text: fmt('syncWarning', { message: (syncData?.detail || syncR.statusText || 'Sync unavailable') }),
        };
      }
    } catch (_) {
      syncStatus = {
        kind: 'error',
        text: fmt('syncFailed', { message: 'Network error' }),
      };
    }

    // Then load all calls (always)
    await loadCalls();
    if (syncStatus) {
      const now = new Date();
      const when = fmt('syncLastUpdated', {
        time: now.toLocaleString(),
      });
      setStatus(syncStatus.kind, syncStatus.text + ' ' + when);
    }
  } catch (e) {
    container.innerHTML = '<p class="result-box error">Sync error: ' + escapeHtml(e.message) + '</p>';
    setStatus('error', fmt('syncFailed', { message: e.message }));
  } finally {
    // Restore button
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }
}

document.getElementById('callsRefresh')?.addEventListener('click', syncAndLoadCalls);

// --- Calendar: upcoming events (showcase) ---
function formatEventDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }) +
    (iso.includes('T') ? ' ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : '');
}

function renderCalendarEvents(events, calendarConfigured) {
  const container = document.getElementById('calendarEventsList');
  if (!container) return;
  if (!events || events.length === 0) {
    if (calendarConfigured === false) {
      container.innerHTML = '<p class="result-box card-desc">' + escapeHtml(t('calendarNotConnected')) + ' <a href="https://developers.google.com/calendar/api/quickstart/python" target="_blank" rel="noopener">Google Calendar API</a>.</p>';
    } else {
      container.innerHTML = '<p class="card-desc">' + escapeHtml(t('noUpcomingEvents')) + '</p>';
    }
    return;
  }
  const descLabel = t('description');
  const openInCal = t('openInCalendar');
  container.innerHTML = events
    .map(
      (ev) => {
        const desc = (ev.description || '').trim();
        const descShort = desc ? desc.slice(0, 120) + (desc.length > 120 ? '…' : '') : '';
        const descBlock = desc ? `<details class="event-desc"><summary>${escapeHtml(descLabel)}</summary><pre class="event-desc-body">${escapeHtml(desc)}</pre></details>` : '';
        const link = ev.htmlLink ? `<a href="${escapeHtml(ev.htmlLink)}" target="_blank" rel="noopener" class="event-link">${escapeHtml(openInCal)}</a>` : '';
        return `
    <div class="calendar-event-item">
      <div class="event-time">${escapeHtml(formatEventDate(ev.start))}</div>
      <div class="event-summary">${escapeHtml(ev.summary)}</div>
      ${descShort ? `<div class="event-desc-preview">${escapeHtml(descShort)}</div>` : ''}
      ${descBlock}
      ${link}
    </div>
  `;
      }
    )
    .join('');
}

async function loadCalendarEvents() {
  const container = document.getElementById('calendarEventsList');
  if (!container) return;
  try {
    const r = await fetch(API + '/calendar/events?days=14');
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || data.message || r.statusText);
    renderCalendarEvents(data.events || [], data.calendar_configured);
  } catch (e) {
    container.innerHTML = '<p class="result-box error">Error: ' + escapeHtml(e.message) + '</p>';
  }
}

document.getElementById('calendarEventsRefresh')?.addEventListener('click', loadCalendarEvents);

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
    setResult(resultEl, t('namePhoneReasonRequired'), 'error');
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
    setResult(resultEl, t('savedId') + ' ' + data.id, 'success');
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

// --- Simulated input type: text vs recording ---
document.getElementById('simInputType')?.addEventListener('change', function () {
  const isText = this.value === 'text';
  const textRow = document.getElementById('simTextRow');
  const recRow = document.getElementById('simRecordingRow');
  if (textRow) textRow.style.display = isText ? '' : 'none';
  if (recRow) recRow.style.display = isText ? 'none' : '';
});
document.getElementById('callRecordingFile')?.addEventListener('change', function () {
  const span = document.getElementById('callRecordingFileName');
  if (span) span.textContent = this.files?.length ? this.files[0].name : 'no file selected';
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
    setResult(resultEl, t('enterCallerSaid'), 'error');
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
      if (data.response_type === 'appointment_booked' && data.appointment_id) {
        lines.push('');
        lines.push('→ Appointment created (see Appointments and Calls).');
      } else if (data.response_type === 'callback') {
        lines.push('');
        lines.push('→ Callback summary created (see Callbacks section).');
        if (typeof loadSummaries === 'function') loadSummaries();
      }
    }
    setResult(resultEl, lines.join('\n'), 'success');
    if (typeof loadCalls === 'function') loadCalls();
    if (data.response_type === 'appointment_booked') {
      setNextStep(nextEl, t('nextAppointmentCreated'));
    } else if (data.response_type === 'callback') {
      setNextStep(nextEl, t('nextSummarySaved'));
    }
  } catch (e) {
    setResult(resultEl, 'Error: ' + (e.message || 'network'), 'error');
  } finally {
    setLoading(btn, false);
  }
});

// --- Test call with recording: transcribe → intent → then full flow (voice/process) ---
document.getElementById('testCallBtnRecording')?.addEventListener('click', async () => {
  const fileInput = document.getElementById('callRecordingFile');
  const phoneEl = document.getElementById('callPhone');
  const resultEl = document.getElementById('testCallResult');
  const nextEl = document.getElementById('testCallNextStep');
  const btn = document.getElementById('testCallBtnRecording');
  const lang = document.getElementById('callRecordingLang')?.value || 'fr';
  const file = fileInput?.files?.[0];
  if (!file) {
    setResult(resultEl, t('chooseRecording'), 'error');
    return;
  }
  btn.dataset.label = btn.textContent;
  setLoading(btn, true);
  setResult(resultEl, 'Transcribing…');
  setNextStep(nextEl, '');
  try {
    const form = new FormData();
    form.append('file', file);
    const r1 = await fetch(API + '/audio/intent?language=' + encodeURIComponent(lang), {
      method: 'POST',
      body: form,
    });
    const data1 = await r1.json().catch(() => ({}));
    if (!r1.ok) throw new Error(data1.detail || data1.message || r1.statusText || (r1.status === 503 ? 'Transcription unavailable. Set OPENAI_API_KEY on the server.' : 'Request failed'));
    const transcript = (data1.transcript || '').trim();
    if (!transcript) {
      setResult(resultEl, t('noSpeechRecording'), 'error');
      setLoading(btn, false);
      return;
    }
    setResult(resultEl, 'Running flow (callback/appointment)…');
    const r2 = await fetch(API + '/voice/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript,
        caller_phone: (phoneEl?.value || '').trim(),
        language: lang,
      }),
    });
    const data = await r2.json().catch(() => ({}));
    if (!r2.ok) throw new Error(data.detail || data.message || r2.statusText || (r2.status === 503 ? 'Service unavailable.' : 'Request failed'));
    const lines = [
      'Transcript: ' + transcript.slice(0, 100) + (transcript.length > 100 ? '…' : ''),
      'Intent: ' + (data.intent || '—'),
      'Action: ' + (data.action || '—'),
      'Response: ' + (data.response_type || '—'),
    ];
    if (data.say_message) lines.push('Message: « ' + (data.say_message || '') + ' »');
    if (data.response_type === 'appointment_booked' && data.appointment_id) {
      lines.push('', '→ Appointment created (see Calendar and Calls).');
    } else if (data.response_type === 'callback') {
      lines.push('', '→ Callback summary created (see Callbacks).');
      if (typeof loadSummaries === 'function') loadSummaries();
    }
    setResult(resultEl, lines.join('\n'), 'success');
    if (typeof loadCalls === 'function') loadCalls();
    if (data.response_type === 'appointment_booked') {
      setNextStep(nextEl, t('nextAppointmentCreated'));
    } else if (data.response_type === 'callback') {
      setNextStep(nextEl, t('nextSummarySee'));
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
    navigator.clipboard.writeText(url).then(() => { alert(t('urlCopied')); });
  }
});

// --- Theme (light/dark; persisted)
const THEME_KEY = 'apen-theme';
function getPreferredTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) return 'light';
  return 'dark';
}
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
}
(function initTheme() {
  setTheme(getPreferredTheme());
})();
document.getElementById('themeToggle')?.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  setTheme(current === 'dark' ? 'light' : 'dark');
});

// --- Language selector (UI + intent/audio; persisted)
(function initLang() {
  const stored = localStorage.getItem(UI_LANG_KEY) || localStorage.getItem(LANG_KEY) || 'en';
  setLang(stored);
  applyTranslations();
})();
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

// Open dropdown when navigating to #details-*
function openDetailsFromHash() {
  const hash = (window.location.hash || '').replace('#', '');
  if (hash === 'details-intent-audio' || hash === 'details-pipeline') {
    const el = document.getElementById(hash);
    if (el && el.tagName === 'DETAILS') el.setAttribute('open', '');
  }
}
window.addEventListener('hashchange', openDetailsFromHash);
openDetailsFromHash();

// Init: health (loads triggered by initLang/setLang), set default date
checkHealth();
const today = new Date().toISOString().slice(0, 10);
const dateEl = document.getElementById('slotsDate');
if (dateEl && !dateEl.value) dateEl.value = today;
setInterval(checkHealth, 30000);
