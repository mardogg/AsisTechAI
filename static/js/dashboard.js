// AsisTech AI Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/login';
    return;
  }

  const username = localStorage.getItem('username') || "User";
  const layoutWelcome = document.getElementById('layoutUserWelcome');
  if (layoutWelcome) layoutWelcome.textContent = `Welcome, ${username}!`;

  const layoutLogoutBtn = document.getElementById('layoutLogoutBtn');
  if (layoutLogoutBtn) {
    layoutLogoutBtn.addEventListener('click', () => {
      if (confirm('Are you sure you want to logout?')) {
        localStorage.clear();
        window.location.href = '/login';
      }
    });
  }

  let currentConversationId = null;
  let conversations = [];

  function showError(msg) {
    const errorToast = document.getElementById('errorToast');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = msg;
    errorToast.classList.remove('hidden');
    setTimeout(() => errorToast.classList.add('hidden'), 5000);
  }

  async function loadConversations() {
    try {
      const response = await fetch('/ai/conversations', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          localStorage.clear();
          window.location.href = '/login';
          return;
        }
        throw new Error('Failed to load conversations');
      }

      conversations = await response.json();
      renderConversations();
    } catch (err) {
      showError(err.message);
    }
  }

  function renderConversations() {
    const list = document.getElementById('conversationsList');
    const loadingEl = document.getElementById('conversationsLoading');
    if (loadingEl) loadingEl.classList.add('hidden');
    
    if (conversations.length === 0) {
      list.innerHTML = '<div class="text-center py-8 text-gray-500"><svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg><p class="text-sm">No conversations yet</p></div>';
      return;
    }

    list.innerHTML = conversations.map(conv => `
      <div class="conversation-item p-3 rounded-lg cursor-pointer hover:bg-purple-50 transition-colors border mb-2 ${conv.id === currentConversationId ? 'bg-purple-100 border-purple-300' : 'border-gray-200'}" data-id="${conv.id}">
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="font-medium text-gray-900 truncate text-sm">${conv.title || 'New Conversation'}</div>
            <div class="text-xs text-gray-500 mt-1">${conv.message_count || 0} messages</div>
          </div>
          <button class="delete-conversation ml-2 text-red-500 hover:text-red-700" data-id="${conv.id}" onclick="event.stopPropagation()">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
          </button>
        </div>
      </div>
    `).join('');

    document.querySelectorAll('.conversation-item').forEach(item => {
      item.addEventListener('click', () => loadConversation(item.dataset.id));
    });

    document.querySelectorAll('.delete-conversation').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Delete this conversation?')) return;
        try {
          await fetch(`/ai/conversations/${btn.dataset.id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (currentConversationId === btn.dataset.id) {
            currentConversationId = null;
            showWelcomeMessage();
          }
          loadConversations();
        } catch (err) {
          showError(err.message);
        }
      });
    });
  }

  async function loadConversation(id) {
    try {
      const response = await fetch(`/ai/conversations/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to load conversation');
      
      const conversation = await response.json();
      currentConversationId = id;
      document.getElementById('chatTitle').textContent = conversation.title || 'AI Assistant';
      
      const messagesContainer = document.getElementById('messagesContainer');
      messagesContainer.innerHTML = conversation.messages.map(msg => renderMessage(msg)).join('');
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      renderConversations();
    } catch (err) {
      showError(err.message);
    }
  }

  function renderMessage(msg) {
    const isUser = msg.role === 'user';
    return `
      <div class="mb-4 flex ${isUser ? 'justify-end' : 'justify-start'}">
        <div class="${isUser ? 'bg-purple-500 text-white' : 'bg-white border border-gray-200'} rounded-lg p-4 max-w-2xl shadow-sm">
          <div class="text-sm whitespace-pre-wrap">${msg.content}</div>
          ${msg.token_count ? `<div class="text-xs mt-2 opacity-60">${msg.token_count} tokens</div>` : ''}
        </div>
      </div>
    `;
  }

  function showWelcomeMessage() {
    const welcomeMsg = document.getElementById('welcomeMessage');
    if (welcomeMsg) {
      document.getElementById('messagesContainer').innerHTML = welcomeMsg.outerHTML;
    } else {
      // Recreate welcome message if it was removed
      document.getElementById('messagesContainer').innerHTML = `
        <div id="welcomeMessage" class="flex items-center justify-center h-full">
          <div class="text-center max-w-2xl px-4">
            <div class="mb-8">
              <div class="inline-flex items-center justify-center w-20 h-20 bg-purple-100 rounded-full mb-4">
                <svg class="w-10 h-10 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                </svg>
              </div>
              <h2 class="text-3xl font-bold text-gray-800 mb-3">Welcome to AsisTech AI</h2>
              <p class="text-lg text-gray-600 mb-8">Your intelligent technical support assistant</p>
            </div>
            <div class="grid md:grid-cols-3 gap-4 text-left">
              <div class="bg-purple-50 p-4 rounded-lg">
                <h3 class="font-semibold text-purple-900 mb-2">💬 Tech Support Chat</h3>
                <p class="text-sm text-gray-600">Get instant help with any tech problem. I'll ask for device details and guide you through solutions.</p>
              </div>
              <div class="bg-purple-50 p-4 rounded-lg">
                <h3 class="font-semibold text-purple-900 mb-2">🔧 Device Diagnostics</h3>
                <p class="text-sm text-gray-600">Run comprehensive diagnostics on your device with step-by-step troubleshooting instructions.</p>
              </div>
              <div class="bg-purple-50 p-4 rounded-lg">
                <h3 class="font-semibold text-purple-900 mb-2">🎥 YouTube Tutorials</h3>
                <p class="text-sm text-gray-600">Find the best video tutorials for fixing your specific tech issue.</p>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  }

  // Chat form handler
  document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;
    
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.innerHTML = '<svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
    
    const welcomeMsg = document.getElementById('welcomeMessage');
    if (welcomeMsg) welcomeMsg.remove();
    
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML += renderMessage({ role: 'user', content: message });
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    input.value = '';
    
    try {
      const response = await fetch('/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: message,
          conversation_id: currentConversationId
        })
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      
      const result = await response.json();
      if (!currentConversationId) {
        currentConversationId = result.conversation_id;
        await loadConversations();
      }
      
      messagesContainer.innerHTML += renderMessage({
        role: 'assistant',
        content: result.assistant_response.content,
        token_count: result.tokens_used
      });
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      
    } catch (err) {
      showError(err.message);
    } finally {
      sendButton.disabled = false;
      sendButton.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg><span class="ml-2">Send</span>';
      input.focus();
    }
  });

  // Diagnostic Modal
  document.getElementById('diagnosticBtn').addEventListener('click', () => {
    document.getElementById('diagnosticModal').classList.remove('hidden');
  });

  document.getElementById('closeDiagnostic').addEventListener('click', () => {
    document.getElementById('diagnosticModal').classList.add('hidden');
  });

  document.getElementById('diagnosticForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const deviceType = document.getElementById('deviceType').value;
    const deviceInfo = document.getElementById('deviceInfo').value;
    const deviceOS = document.getElementById('deviceOS').value;
    const deviceProblem = document.getElementById('deviceProblem').value;
    
    document.getElementById('diagnosticModal').classList.add('hidden');
    
    try {
      const response = await fetch('/ai/device-diagnostic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          device_type: deviceType,
          device_info: deviceInfo,
          operating_system: deviceOS,
          problem_description: deviceProblem
        })
      });
      
      if (!response.ok) throw new Error('Diagnostic failed');
      
      const result = await response.json();
      const messagesContainer = document.getElementById('messagesContainer');
      messagesContainer.innerHTML += renderMessage({
        role: 'assistant',
        content: result.content
      });
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      
    } catch (err) {
      showError(err.message);
    }
  });

  // YouTube Modal
  document.getElementById('youtubeBtn').addEventListener('click', () => {
    document.getElementById('youtubeModal').classList.remove('hidden');
  });

  document.getElementById('closeYoutube').addEventListener('click', () => {
    document.getElementById('youtubeModal').classList.add('hidden');
  });

  document.getElementById('youtubeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const youtubeDevice = document.getElementById('youtubeDevice').value;
    const youtubeProblem = document.getElementById('youtubeProblem').value;
    
    document.getElementById('youtubeModal').classList.add('hidden');
    
    try {
      const response = await fetch('/ai/youtube-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          problem_description: youtubeProblem,
          device_info: youtubeDevice
        })
      });
      
      if (!response.ok) throw new Error('YouTube search failed');
      
      const result = await response.json();
      const messagesContainer = document.getElementById('messagesContainer');
      messagesContainer.innerHTML += renderMessage({
        role: 'assistant',
        content: result.content
      });
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      
      // Open YouTube in new tab
      if (result.youtube_url) {
        window.open(result.youtube_url, '_blank');
      }
      
    } catch (err) {
      showError(err.message);
    }
  });

  // New conversation button
  document.getElementById('newConversationBtn').addEventListener('click', () => {
    currentConversationId = null;
    document.getElementById('chatTitle').textContent = 'AsisTech AI Assistant';
    showWelcomeMessage();
    renderConversations();
    document.getElementById('messageInput').focus();
  });

  // Initial load
  loadConversations();
});
