import { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import Sidebar from './components/Sidebar';
import UserModal from './components/UserModal';
import LoginModal from './components/LoginModal';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [role, setRole] = useState('anonymous');
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const user = {
    name: 'John Doe',
    position: 'Developer',
    unit: 'IT Department',
    isAdmin: true,
  };

  useEffect(() => {
    if (isLoggedIn) {
      const storedConversations = JSON.parse(localStorage.getItem('conversations')) || [];
      setConversations(storedConversations);
      if (storedConversations.length > 0) {
        setCurrentConversationId(storedConversations[0].id);
      } else {
        createNewConversation();
      }
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }
  }, [conversations]);

  const createNewConversation = () => {
    const newId = Date.now().toString();
    const newConv = { id: newId, title: 'New Chat', messages: [] };
    setConversations([newConv, ...conversations]);
    setCurrentConversationId(newId);
  };

  const handleSendMessage = async (text) => {
    // Đẩy tin nhắn người dùng vào hội thoại hiện tại
    setConversations(prev => prev.map(conv => {
      if (conv.id === currentConversationId) {
        const newMessages = [...conv.messages, { sender: 'user', text }];
        const newTitle = conv.messages.length === 0 ? text.slice(0, 30) + (text.length > 30 ? '...' : '') : conv.title;
        return { ...conv, title: newTitle, messages: newMessages };
      }
      return conv;
    }));

    setIsLoading(true);

    // Lấy session cho cuộc hội thoại (anonymous vẫn dùng session local, nhưng không lưu server)
    const sessionKey = `session:${currentConversationId}`;
    const sessionId = localStorage.getItem(sessionKey);

    try {
      // Dùng SSE stream
      const headers = { 'Content-Type': 'application/json' };
      const token = localStorage.getItem('auth:token');
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers,
        body: JSON.stringify({ query: text, session_id: sessionId || null })
      });

      if (!res.ok || !res.body) throw new Error('Network response was not ok');

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botAccum = '';

      const appendBot = (chunkText) => {
        botAccum += chunkText;
        setConversations(prev => prev.map(conv => {
          if (conv.id === currentConversationId) {
            // Nếu tin nhắn bot chưa có, thêm mới; nếu có rồi, cập nhật nội dung
            const msgs = [...conv.messages];
            const last = msgs[msgs.length - 1];
            if (!last || last.sender !== 'bot' || !last.streaming) {
              msgs.push({ sender: 'bot', text: chunkText, streaming: true });
            } else {
              msgs[msgs.length - 1] = { ...last, text: botAccum, streaming: true };
            }
            return { ...conv, messages: msgs };
          }
          return conv;
        }));
      };

      // Đọc từng chunk SSE
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const textChunk = decoder.decode(value, { stream: true });
        const lines = textChunk.split(/\r?\n/);
        for (const line of lines) {
          if (!line) continue;
          if (line.startsWith('data: ')) {
            const payload = line.slice(6);
            if (payload === '[DONE]') continue;
            appendBot(payload);
          }
        }
      }

      // Kết thúc streaming: bỏ cờ streaming
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          const msgs = [...conv.messages];
          if (msgs.length && msgs[msgs.length - 1].streaming) {
            msgs[msgs.length - 1] = { sender: 'bot', text: msgs[msgs.length - 1].text };
          }
          return { ...conv, messages: msgs };
        }
        return conv;
      }));

      // Nếu đã đăng nhập: cập nhật local cache từ server có thể thực hiện here (tối giản: để lần tải lịch sử sau)
    } catch (err) {
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return { ...conv, messages: [...conv.messages, { sender: 'bot', text: 'Có lỗi khi gọi API.' }] };
        }
        return conv;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const selectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const deleteConversation = (id) => {
    const updated = conversations.filter(conv => conv.id !== id);
    setConversations(updated);
    if (currentConversationId === id) {
      if (updated.length > 0) {
        setCurrentConversationId(updated[0].id);
      } else {
        createNewConversation();
      }
    }
  };

  const renameConversation = (id, newTitle) => {
    setConversations(prev => prev.map(conv => 
      conv.id === id ? { ...conv, title: newTitle } : conv
    ));
  };

  const filteredConversations = conversations.filter(conv => 
    conv.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const currentMessages = conversations.find(conv => conv.id === currentConversationId)?.messages || [];

  const handleLogout = () => {
    setIsLoggedIn(false);
    setIsUserModalOpen(false);
    localStorage.clear();
    setRole('anonymous');
  };

  return (
    <div className="h-screen flex bg-dark-slate">
      <Sidebar 
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        conversations={filteredConversations}
        currentId={currentConversationId}
        onSelect={selectConversation}
        onNewChat={createNewConversation}
        onDelete={deleteConversation}
        onRename={renameConversation}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        isAdmin={user.isAdmin}
      />
      <div className="flex-1 flex flex-col">
        <Header 
          isLoggedIn={isLoggedIn}
          onOpenLoginModal={() => setIsLoginModalOpen(true)}
          onOpenUserModal={() => setIsUserModalOpen(true)}
        />
        <ChatWindow messages={currentMessages.concat(isLoading ? [{ sender: 'bot', text: 'Đang xử lý...' }] : [])} />
        <InputBox onSendMessage={handleSendMessage} />
      </div>
      {isUserModalOpen && (
        <UserModal user={user} onClose={() => setIsUserModalOpen(false)} onLogout={handleLogout} />
      )}
      {isLoginModalOpen && (
        <LoginModal onClose={() => setIsLoginModalOpen(false)} onLogin={() => {
          setIsLoginModalOpen(false);
          setIsLoggedIn(true);
          const savedRole = localStorage.getItem('auth:role') || 'user';
          setRole(savedRole);
        }} />
      )}
    </div>
  );
}

export default App;