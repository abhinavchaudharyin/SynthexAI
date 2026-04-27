const API_BASE = 'http://127.0.0.1:8000';
let conversationHistory = [];
let isProcessing = false;
let isExpanded = false;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let uploadedImageBase64 = null;
let uploadedImageFile = null;

// ========= OPEN / CLOSE =========
function openChat() {
  document.getElementById('mainPage').style.display = 'none';
  document.getElementById('floatBtn').style.display = 'none';
  document.getElementById('widget').style.display = 'flex';
  document.getElementById('queryInput').focus();
}

function closeChat() {
  document.getElementById('widget').style.display = 'none';
  document.getElementById('mainPage').style.display = 'flex';
  document.getElementById('floatBtn').style.display = 'flex';
}

// ========= EXPAND / COLLAPSE =========
function toggleExpand() {
  isExpanded = !isExpanded;
  const box = document.getElementById('widgetBox');
  const icon = document.getElementById('expandIcon');
  if (isExpanded) {
    box.classList.add('expanded');
    icon.innerHTML = '<path d="M8 3v3a2 2 0 01-2 2H3m18 0h-3a2 2 0 01-2-2V3m0 18v-3a2 2 0 012-2h3M3 16h3a2 2 0 012 2v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
  } else {
    box.classList.remove('expanded');
    icon.innerHTML = '<path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
  }
}

// ========= SEND QUERY =========
async function sendQuery() {
  const input = document.getElementById('queryInput');
  const query = input.value.trim();
  if (!query && !uploadedImageBase64) return;
  if (isProcessing) return;

  isProcessing = true;
  input.value = '';
  autoResize(input);
  document.getElementById('sendBtn').disabled = true;

  if (uploadedImageBase64 && uploadedImageFile) {
    appendUserMessage(query || 'Extract text from this image', uploadedImageBase64);
    const ocrText = await doOCR();
    const finalQuery = ocrText ? `${query ? query + '\n\n' : ''}Image content: ${ocrText}` : query;
    removeImage();
    await processQuery(finalQuery);
  } else {
    appendUserMessage(query);
    await processQuery(query);
  }
}

async function doOCR() {
  try {
    const formData = new FormData();
    formData.append('image', uploadedImageFile);
    const res = await fetch(`${API_BASE}/ocr`, { method: 'POST', body: formData });
    const data = await res.json();
    return data.success ? data.text : '';
  } catch {
    return '';
  }
}

async function processQuery(query) {
  showProcessing(true);
  setStatus('Thinking...');

  await animateStep(1, 'Checking guardrails...');
  await sleep(400);
  await animateStep(2, 'Searching web...');
  await sleep(500);
  await animateStep(3, 'Consulting Groq · Gemini · Mistral...');
  setChipActive(['chip-groq', 'chip-gemini', 'chip-mistral', 'chip-search']);

  const typingId = showTyping();

  try {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        user_id: 'user_' + getSessionId(),
        history: conversationHistory
      })
    });

    await animateStep(4, 'Synthesizing answer...');
    removeTyping(typingId);
    showProcessing(false);

    // Streaming bubble banao
    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg ai';
    msgDiv.innerHTML = `
      <div class="msg-role">SynthexAI</div>
      <div class="msg-bubble" id="streaming-bubble"></div>
      <div class="msg-meta" id="streaming-meta"></div>
    `;
    document.getElementById('messages').appendChild(msgDiv);

    const bubble = document.getElementById('streaming-bubble');
    let fullText = '';
    let metaData = null;

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Last incomplete line buffer mein rakho
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);

          if (data.type === 'meta') {
            metaData = data;
            updateChips(data.models_used, data.models_skipped);
            showConfidence(data.models_used);
            if (data.sources && data.sources.length > 0) {
              showSources(data.sources);
            } else {
              hideSources();
            }
            updateFooter(data.models_used, data.models_skipped);

          } else if (data.type === 'token') {
            fullText += data.text;
            bubble.innerHTML = formatAnswer(fullText);
            scrollToBottom();

          } else if (data.type === 'done') {
            conversationHistory.push({ role: 'user', content: query });
            conversationHistory.push({ role: 'assistant', content: fullText });

            const meta = document.getElementById('streaming-meta');
            if (metaData && meta) {
              const tags = (metaData.models_used || []).map(m =>
                `<span class="model-tag">${m}</span>`
              ).join('');
              const skippedText = metaData.models_skipped && metaData.models_skipped.length > 0
                ? ` · skipped: ${metaData.models_skipped.join(', ')}`
                : '';
              meta.innerHTML = `<div class="msg-model-tag">${tags}</div><span>${skippedText}</span>`;
            }

            bubble.removeAttribute('id');
            document.getElementById('streaming-meta')?.removeAttribute('id');
            setStatus('All systems online');
          }
        } catch (e) {
          // Invalid JSON — skip
        }
      }
    }

  } catch (err) {
    removeTyping(typingId);
    showProcessing(false);
    appendAIMessage('⚠️ Could not connect to SynthexAI backend. Make sure the server is running on port 8000.', [], []);
    setStatus('Connection error');
    resetChips();
  }

  isProcessing = false;
  document.getElementById('sendBtn').disabled = false;
  document.getElementById('queryInput').focus();
}

function sendSuggestion(text) {
  document.getElementById('queryInput').value = text;
  sendQuery();
}

// ========= MESSAGES =========
function appendUserMessage(text, imageBase64 = null) {
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg user';

  let imgHtml = '';
  if (imageBase64) {
    imgHtml = `<img class="msg-image" src="data:image/jpeg;base64,${imageBase64}" alt="uploaded"/>`;
  }

  div.innerHTML = `
    <div class="msg-role">You</div>
    ${imgHtml}
    <div class="msg-bubble">${escapeHtml(text)}</div>
  `;
  messages.appendChild(div);
  scrollToBottom();
}

function appendAIMessage(text, modelsUsed = [], modelsSkipped = []) {
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg ai';

  const modelTags = (modelsUsed || []).map(m =>
    `<span class="model-tag">${m}</span>`
  ).join('');

  const skippedText = modelsSkipped && modelsSkipped.length > 0
    ? ` · skipped: ${modelsSkipped.join(', ')}`
    : '';

  div.innerHTML = `
    <div class="msg-role">SynthexAI</div>
    <div class="msg-bubble">${formatAnswer(text)}</div>
    <div class="msg-meta">
      <div class="msg-model-tag">${modelTags}</div>
      <span>${skippedText}</span>
    </div>
  `;
  messages.appendChild(div);
  scrollToBottom();
}

function showTyping() {
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg ai';
  const id = 'typing_' + Date.now();
  div.id = id;
  div.innerHTML = `
    <div class="msg-role">SynthexAI</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  messages.appendChild(div);
  scrollToBottom();
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ========= PROCESSING STEPS =========
function showProcessing(show) {
  document.getElementById('processingBar').style.display = show ? 'block' : 'none';
  if (show) {
    for (let i = 1; i <= 4; i++) {
      const step = document.getElementById('step' + i);
      step.classList.remove('active', 'done');
      step.querySelector('.proc-dot').classList.remove('active', 'done');
    }
  }
}

async function animateStep(stepNum, text) {
  if (stepNum > 1) {
    const prev = document.getElementById('step' + (stepNum - 1));
    prev.classList.remove('active');
    prev.classList.add('done');
    prev.querySelector('.proc-dot').classList.remove('active');
    prev.querySelector('.proc-dot').classList.add('done');
  }
  const step = document.getElementById('step' + stepNum);
  step.classList.add('active');
  step.querySelector('.proc-dot').classList.add('active');
  document.getElementById('step' + stepNum + 'text').textContent = text;
}

// ========= MODEL CHIPS =========
function setChipActive(ids) {
  ['chip-groq', 'chip-gemini', 'chip-mistral', 'chip-search'].forEach(id => {
    document.getElementById(id).className = 'model-chip';
  });
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
  });
}

function updateChips(used, skipped) {
  const chipMap = {
    'Groq (Llama 3)': 'chip-groq',
    'Gemini 1.5 Flash': 'chip-gemini',
    'Mistral': 'chip-mistral'
  };

  Object.values(chipMap).forEach(id => {
    document.getElementById(id).className = 'model-chip';
  });

  (used || []).forEach(model => {
    const id = chipMap[model];
    if (id) document.getElementById(id).classList.add('used');
  });

  (skipped || []).forEach(model => {
    const id = chipMap[model];
    if (id) document.getElementById(id).classList.add('skipped');
  });
}

function resetChips() {
  ['chip-groq', 'chip-gemini', 'chip-mistral', 'chip-search'].forEach(id => {
    document.getElementById(id).className = 'model-chip';
  });
}

function showConfidence(modelsUsed) {
  const badge = document.getElementById('confidenceBadge');
  const val = document.getElementById('confidenceVal');
  if (!modelsUsed || modelsUsed.length === 0) {
    badge.style.display = 'none';
    return;
  }
  const confidence = Math.round(60 + (modelsUsed.length * 13));
  val.textContent = confidence + '%';
  badge.style.display = 'flex';
}

// ========= SOURCES =========
function showSources(sources) {
  const panel = document.getElementById('sourcesPanel');
  const list = document.getElementById('sourcesList');
  list.innerHTML = '';
  sources.slice(0, 4).forEach(s => {
    const a = document.createElement('a');
    a.className = 'source-link';
    a.href = s.url;
    a.target = '_blank';
    a.textContent = s.title;
    list.appendChild(a);
  });
  panel.style.display = 'block';
}

function hideSources() {
  document.getElementById('sourcesPanel').style.display = 'none';
}

// ========= VOICE INPUT =========
async function toggleVoice() {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/wav' });
      await transcribeAudio(blob);
      stream.getTracks().forEach(t => t.stop());
    };

    mediaRecorder.start();
    isRecording = true;
    document.getElementById('micBtn').classList.add('recording');
    setStatus('Recording...');
  } catch (err) {
    setStatus('Microphone access denied');
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    document.getElementById('micBtn').classList.remove('recording');
    setStatus('Processing voice...');
  }
}

async function transcribeAudio(blob) {
  try {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.wav');
    const res = await fetch(`${API_BASE}/voice-input`, { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success && data.text) {
      document.getElementById('queryInput').value = data.text;
      autoResize(document.getElementById('queryInput'));
      setStatus('Voice transcribed');
    } else {
      setStatus('Could not transcribe — try again');
    }
  } catch {
    setStatus('Voice transcription failed');
  }
}

// ========= IMAGE UPLOAD =========
function triggerImageUpload() {
  document.getElementById('imageInput').click();
}

function handleImageUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  uploadedImageFile = file;

  const reader = new FileReader();
  reader.onload = e => {
    const base64 = e.target.result.split(',')[1];
    uploadedImageBase64 = base64;
    const preview = document.getElementById('imagePreview');
    document.getElementById('previewImg').src = e.target.result;
    preview.style.display = 'flex';
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  uploadedImageBase64 = null;
  uploadedImageFile = null;
  document.getElementById('imagePreview').style.display = 'none';
  document.getElementById('imageInput').value = '';
}

// ========= UI HELPERS =========
function setStatus(text) {
  document.getElementById('statusText').innerHTML = `<span class="status-dot"></span>${text}`;
}

function updateFooter(used, skipped) {
  const el = document.getElementById('lastModelInfo');
  if (!used || used.length === 0) { el.textContent = ''; return; }
  el.textContent = `Used: ${used.join(' · ')}${skipped && skipped.length ? ' · Skipped: ' + skipped.join(', ') : ''}`;
}

function scrollToBottom() {
  const messages = document.getElementById('messages');
  messages.scrollTop = messages.scrollHeight;
}

function handleKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendQuery();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function formatAnswer(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/### (.*?)(\n|$)/g, '<h4 style="font-family:Times New Roman,serif;font-size:1rem;font-weight:700;margin:14px 0 4px;color:#F0F0F8;">$1</h4>')
    .replace(/## (.*?)(\n|$)/g, '<h3 style="font-family:Times New Roman,serif;font-size:1.1rem;font-weight:700;margin:16px 0 4px;color:#F0F0F8;">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.08);padding:1px 5px;border-radius:4px;font-family:monospace;font-size:0.82em">$1</code>')
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:8px 0;">')
    .replace(/^\d+\. (.*)/gm, '<div style="margin:1px 0;padding-left:16px;font-family:Times New Roman,serif;font-size:0.95rem;">$1</div>')
    .replace(/^- (.*)/gm, '<div style="margin:1px 0;padding-left:16px;font-family:Times New Roman,serif;font-size:0.95rem;">• $1</div>')
    .replace(/^\|(.+)\|$/gm, (match) => {
      const cells = match.split('|').filter(c => c.trim());
      if (cells.every(c => c.trim().match(/^[-:\s]+$/))) return '';
      return '<div style="display:flex;gap:8px;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.06);">' +
        cells.map(c => `<span style="flex:1;font-family:Times New Roman,serif;font-size:0.88rem;color:#F0F0F8;">${c.trim()}</span>`).join('') +
        '</div>';
    })
    .replace(/\n{2,}/g, '<br>')
    .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function getSessionId() {
  let id = sessionStorage.getItem('synthex_session');
  if (!id) {
    id = Math.random().toString(36).slice(2);
    sessionStorage.setItem('synthex_session', id);
  }
  return id;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}