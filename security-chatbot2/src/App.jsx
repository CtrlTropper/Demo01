import { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import Sidebar from './components/Sidebar';
import UserModal from './components/UserModal';
import Login from './components/Login';

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [user, setUser] = useState({ name: 'Guest', position: 'Guest', unit: '', isAdmin: false });
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchMe = async (tkn) => {
    try {
      const res = await fetch(`${API_BASE}/me`, {
        headers: { 'Authorization': `Bearer ${tkn}` }
      });
      if (!res.ok) throw new Error('Failed to get profile');
      const data = await res.json();
      setUser({ name: data.username, position: 'User', unit: '', isAdmin: !!data.is_admin });
    } catch (e) {
      setUser({ name: 'Guest', position: 'Guest', unit: '', isAdmin: false });
    }
  };

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      setIsLoggedIn(true);
      fetchMe(savedToken);
    }
  }, []);

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

  const handleSendMessage = (text) => {
    setConversations(prev => {
      const updated = prev.map(conv => {
        if (conv.id === currentConversationId) {
          const newMessages = [...conv.messages, { sender: 'user', text }];
          const newTitle = conv.messages.length === 0 ? text.slice(0, 30) + (text.length > 30 ? '...' : '') : conv.title;
          return { ...conv, title: newTitle, messages: newMessages };
        }
        return conv;
      });
      return updated;
    });

    setIsLoading(true);
    fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ query: text }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const txt = await res.text();
          throw new Error(txt || 'Request failed');
        }
        return res.json();
      })
      .then(data => {
        const botText = data?.response || 'Không nhận được phản hồi.';
        setConversations(prevUpdated => prevUpdated.map(c => {
          if (c.id === currentConversationId) {
            return { ...c, messages: [...c.messages, { sender: 'bot', text: botText }] };
          }
          return c;
        }));
      })
      .catch(err => {
        setConversations(prevUpdated => prevUpdated.map(c => {
          if (c.id === currentConversationId) {
            return { ...c, messages: [...c.messages, { sender: 'bot', text: `Lỗi: ${err.message}` }] };
          }
          return c;
        }));
      })
      .finally(() => setIsLoading(false));
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
    setIsModalOpen(false);
    setToken('');
    localStorage.clear();
    setUser({ name: 'Guest', position: 'Guest', unit: '', isAdmin: false });
  };

  if (!isLoggedIn) {
    return <Login onLogin={(sessionToken) => { localStorage.setItem('token', sessionToken); setToken(sessionToken); setIsLoggedIn(true); fetchMe(sessionToken); }} />;
  }

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
        <Header onOpenModal={() => setIsModalOpen(true)} />
        <ChatWindow messages={currentMessages.concat(isLoading ? [{ sender: 'bot', text: 'Đang xử lý...' }] : [])} />
        <InputBox onSendMessage={handleSendMessage} />
      </div>
      {isModalOpen && (
        <UserModal user={user} onClose={() => setIsModalOpen(false)} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;