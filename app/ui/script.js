const chatEl = document.getElementById('chat');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const clearBtn = document.getElementById('clearMemory');
const clearVectorstoreBtn = document.getElementById('clearVectorstore');
const newChatBtn = document.getElementById('newChat');
const chatListEl = document.getElementById('chatList');
const pdfUploadEl = document.getElementById('pdfUpload');
const uploadStatusEl = document.getElementById('uploadStatus');

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

function addMsg(role, text, meta, isTyping = false) {
  const row = document.createElement('div');
  row.className = `msg ${role}`;
  const textContent = isTyping ? '<span class="typing-animation">Generating answer</span>' : escapeHtml(text);
  row.innerHTML = `
    <div class="avatar">${role === 'me' ? 'You' : 'AI'}</div>
    <div>
      <div class="bubble">${textContent}</div>
      ${meta ? `<div class="meta">${meta}</div>` : ''}
    </div>`;
  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;
  return row;
}

function escapeHtml(str) {
  return str.replace(/[&<>"]+/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[s]));
}

async function ask(question) {
  const session_id = getSessionId();
  setSessionId(session_id);
  addMsg('me', question);
  inputEl.value = '';
  
  // Add typing indicator
  const typingRow = addMsg('bot', 'Generating answer', null, true);
  
  try {
    const resp = await fetch('/v1/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id })
    });
    
    // Remove typing indicator
    typingRow.remove();
    
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
    typingRow.remove();
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

async function clearVectorstore() {
  if (!confirm('Are you sure you want to clear all ingested PDFs? This action cannot be undone.')) {
    return;
  }
  try {
    const resp = await fetch('/v1/clear_vectorstore', {
      method: 'POST'
    });
    if (!resp.ok) {
      const text = await resp.text();
      addMsg('bot', `Clear failed: ${resp.status} ${text}`);
      return;
    }
    const data = await resp.json();
    addMsg('bot', data.message || `Successfully cleared ${data.deleted_chunks || 0} chunks from vector store.`);
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
clearVectorstoreBtn.addEventListener('click', clearVectorstore);
newChatBtn.addEventListener('click', () => { const id = uuid(); setSessionId(id); upsertChatTitle(id, 'New chat'); chatEl.innerHTML=''; });

// PDF upload handler
pdfUploadEl.addEventListener('change', async (e) => {
  const files = Array.from(e.target.files);
  if (files.length === 0) return;
  
  uploadStatusEl.textContent = files.length === 1 ? 'Uploading...' : `Uploading ${files.length} files...`;
  uploadStatusEl.style.color = '#3b82f6';
  
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  try {
    const resp = await fetch('/v1/upload', {
      method: 'POST',
      body: formData
    });
    
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text);
    }
    
    const data = await resp.json();
    const summary = data.summary;
    
    if (summary.successful === files.length) {
      uploadStatusEl.textContent = `✓ ${summary.successful} file(s), ${summary.total_chunks_ingested} chunks`;
      uploadStatusEl.style.color = '#10b981';
    } else if (summary.successful > 0) {
      uploadStatusEl.textContent = `⚠ ${summary.successful}/${summary.total_files} succeeded`;
      uploadStatusEl.style.color = '#f59e0b';
    } else {
      uploadStatusEl.textContent = '✗ All uploads failed';
      uploadStatusEl.style.color = '#ef4444';
    }
    
    // Show detailed results in chat
    if (summary.successful > 0) {
      const successMsgs = data.results.filter(r => r.status === 'success')
        .map(r => `• ${r.filename}: ${r.chunks_ingested} chunks`)
        .join('\n');
      addMsg('bot', `Successfully uploaded ${summary.successful} PDF(s):\n${successMsgs}`);
    }
    
    if (summary.failed > 0) {
      const errorMsgs = data.results.filter(r => r.status === 'error')
        .map(r => `• ${r.filename}: ${r.message}`)
        .join('\n');
      addMsg('bot', `Failed to upload ${summary.failed} file(s):\n${errorMsgs}`);
    }
    
    // Clear file input
    e.target.value = '';
    
    // Clear status after 5 seconds
    setTimeout(() => {
      uploadStatusEl.textContent = '';
    }, 5000);
  } catch (e) {
    uploadStatusEl.textContent = '✗ Upload failed';
    uploadStatusEl.style.color = '#ef4444';
    addMsg('bot', `Upload failed: ${e.message}`);
    
    setTimeout(() => {
      uploadStatusEl.textContent = '';
    }, 5000);
  }
});

// init
setSessionId(getSessionId());
renderChatList();
loadHistory();

