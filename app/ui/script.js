const chatEl = document.getElementById('chat');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const clearBtn = document.getElementById('clearMemory');
const newChatBtn = document.getElementById('newChat');
const chatListEl = document.getElementById('chatList');

function uuid() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

function getSessionId() {
  let id = localStorage.getItem('chatpdf.session_id');
  if (!id) {
    id = uuid();
    localStorage.setItem('chatpdf.session_id', id);
  }
  return id;
}

function setSessionId(id) {
  localStorage.setItem('chatpdf.session_id', id);
}

function getChats() {
  try { return JSON.parse(localStorage.getItem('chatpdf.chats') || '[]'); } catch { return []; }
}
function setChats(chats) {
  localStorage.setItem('chatpdf.chats', JSON.stringify(chats));
}
function upsertChatTitle(id, title) {
  const chats = getChats();
  const idx = chats.findIndex(c => c.id === id);
  const item = { id, title: title || 'New chat', updatedAt: new Date().toISOString() };
  if (idx >= 0) chats[idx] = { ...chats[idx], ...item };
  else chats.unshift(item);
  setChats(chats);
  renderChatList();
}
function renderChatList() {
  const id = getSessionId();
  const chats = getChats();
  chatListEl.innerHTML = '';
  chats.forEach(c => {
    const el = document.createElement('div');
    el.className = 'chat-item' + (c.id === id ? ' active' : '');
    el.innerHTML = `<div class="title">${escapeHtml(c.title || 'New chat')}</div><div class="meta">${new Date(c.updatedAt).toLocaleString()}</div>`;
    el.onclick = () => switchChat(c.id);
    chatListEl.appendChild(el);
  });
}
async function switchChat(id) {
  setSessionId(id);
  renderChatList();
  await loadHistory();
}
async function loadHistory() {
  chatEl.innerHTML = '';
  const session_id = getSessionId();
  try {
    const resp = await fetch(`/v1/history?session_id=${encodeURIComponent(session_id)}`);
    if (!resp.ok) return;
    const data = await resp.json();
    (data.history || []).forEach(turn => {
      addMsg('me', turn.question);
      addMsg('bot', turn.answer, (turn.sources && turn.sources.length) ? `sources: ${turn.sources.join(', ')}` : '');
    });
  } catch {}
}

function addMsg(role, text, meta) {
  const row = document.createElement('div');
  row.className = `msg ${role}`;
  row.innerHTML = `
    <div class="avatar">${role === 'me' ? 'You' : 'AI'}</div>
    <div>
      <div class="bubble">${escapeHtml(text)}</div>
      ${meta ? `<div class="meta">${meta}</div>` : ''}
    </div>`;
  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/[&<>"]+/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[s]));
}

async function ask(question) {
  const session_id = getSessionId();
  setSessionId(session_id);
  addMsg('me', question);
  inputEl.value = '';
  try {
    const resp = await fetch('/v1/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id })
    });
    if (!resp.ok) {
      const text = await resp.text();
      addMsg('bot', `Error ${resp.status}: ${text}`);
      return;
    }
    const data = await resp.json();
    const meta = [];
    if (Array.isArray(data.sources) && data.sources.length) meta.push(`sources: ${data.sources.join(', ')}`);
    if (Array.isArray(data.plan) && data.plan.length) meta.push(`plan: ${JSON.stringify(data.plan)}`);
    addMsg('bot', data.answer || '(no answer)', meta.join(' | '));
    // Set chat title from first question
    const chats = getChats();
    const has = chats.find(c => c.id === session_id);
    if (!has) upsertChatTitle(session_id, question.slice(0, 60));
    else upsertChatTitle(session_id, has.title || question.slice(0, 60));
  } catch (e) {
    addMsg('bot', `Request failed: ${e}`);
  }
}

async function clearMemory() {
  const session_id = getSessionId();
  try {
    const resp = await fetch('/v1/clear_memory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id })
    });
    if (!resp.ok) {
      const text = await resp.text();
      addMsg('bot', `Clear failed: ${resp.status} ${text}`);
      return;
    }
    addMsg('bot', 'Memory cleared for this session.');
  } catch (e) {
    addMsg('bot', `Request failed: ${e}`);
  }
}

sendBtn.addEventListener('click', () => {
  const q = inputEl.value.trim();
  if (q) ask(q);
});
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); const q = inputEl.value.trim(); if (q) ask(q); }
});
clearBtn.addEventListener('click', clearMemory);
newChatBtn.addEventListener('click', () => { const id = uuid(); setSessionId(id); upsertChatTitle(id, 'New chat'); chatEl.innerHTML=''; });

// init
setSessionId(getSessionId());
renderChatList();
loadHistory();

