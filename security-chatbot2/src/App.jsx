import { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import Sidebar from './components/Sidebar';
import DocumentManagerModal from './components/DocumentManagerModal';

function App() {
  // Loại bỏ đăng nhập/phân quyền
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeDoc, setActiveDoc] = useState(null); // { id, pdf_name }
  const [abortController, setAbortController] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  // Không dùng modal người dùng/đăng nhập
  const [isDocsOpen, setIsDocsOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [docsRefreshKey, setDocsRefreshKey] = useState(0);

  // Không cần thông tin người dùng

  useEffect(() => {
    const storedConversations = JSON.parse(localStorage.getItem('conversations')) || [];
    setConversations(storedConversations);
    if (storedConversations.length > 0) {
      setCurrentConversationId(storedConversations[0].id);
    } else {
      createNewConversation();
    }
  }, []);

  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }
  }, [conversations]);

  const createNewConversation = () => {
    // Nếu đã có cuộc trò chuyện trống, chỉ chọn nó thay vì tạo mới
    const existingEmpty = conversations.find(c => (c?.messages?.length || 0) === 0);
    if (existingEmpty) {
      setCurrentConversationId(existingEmpty.id);
      return;
    }
    const newId = Date.now().toString();
    const newConv = { id: newId, title: 'New Chat', messages: [] };
    setConversations([newConv, ...conversations]);
    setCurrentConversationId(newId);
  };

  const handleSendMessage = async (text) => {
    if (isLoading) return;
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
      const controller = new AbortController();
      setAbortController(controller);
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers,
        body: JSON.stringify({ query: text, session_id: sessionId || null, doc_id: activeDoc?.id || null, pdf_name: activeDoc?.id ? null : (activeDoc?.pdf_name || null) }),
        signal: controller.signal
      });

      if (!res.ok || !res.body) throw new Error('Network response was not ok');

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botAccum = '';
      let sseBuffer = '';

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

      // Đọc từng chunk SSE, buffer và tách theo sự kiện (\n\n)
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        sseBuffer += decoder.decode(value, { stream: true });
        let eventEndIndex;
        while ((eventEndIndex = sseBuffer.indexOf('\n\n')) !== -1) {
          const rawEvent = sseBuffer.slice(0, eventEndIndex);
          sseBuffer = sseBuffer.slice(eventEndIndex + 2);
          // Một sự kiện SSE có thể gồm nhiều dòng 'data:'
          const dataLines = rawEvent.split(/\r?\n/).filter(l => l.startsWith('data:'));
          // Loại bỏ đúng 1 khoảng trắng sau 'data:' (nếu có) để tránh double-space, giữ các khoảng trắng khác
          const payload = dataLines
            .map(l => {
              const after = l.slice(5);
              return after.startsWith(' ') ? after.slice(1) : after;
            })
            .join('\n');
          if (!payload) continue;
          if (payload === '[DONE]') {
            // Bỏ qua, vòng while ngoài sẽ kết thúc khi reader.done = true
            continue;
          }
          appendBot(payload);
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
      if (err?.name !== 'AbortError') {
        setConversations(prev => prev.map(conv => {
          if (conv.id === currentConversationId) {
            return { ...conv, messages: [...conv.messages, { sender: 'bot', text: 'Có lỗi khi gọi API.' }] };
          }
          return conv;
        }));
      }
    } finally {
      setIsLoading(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (abortController) {
      try { abortController.abort(); } catch (e) {}
    }
  };

  const handleUploadPdf = async (file) => {
    if (!file) return;
    setUploading(true);
    setUploadProgress(0);
    try {
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload-pdf');
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            setUploadProgress((e.loaded / e.total) * 100);
          }
        };
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              if (data && data.doc_id && data.pdf_name) {
                setActiveDoc({ id: data.doc_id, pdf_name: data.pdf_name });
              } else if (data && data.message === 'PDF already embedded' && data.doc_id) {
                setActiveDoc({ id: data.doc_id, pdf_name: data.pdf_name });
              }
              resolve();
            } catch (err) {
              reject(err);
            }
          } else {
            reject(new Error('Upload failed'));
          }
        };
        xhr.onerror = () => reject(new Error('Network error'));
        const form = new FormData();
        form.append('file', file);
        xhr.send(form);
      });
      setDocsRefreshKey((k) => k + 1);
    } catch (e) {
      console.error(e);
      alert('Tải PDF thất bại');
    } finally {
      setUploading(false);
      setUploadProgress(0);
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

  // Không còn đăng xuất

  return (
    <div className="h-screen w-screen flex bg-dark-slate">
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
        hasEmptyChat={conversations.some(c => (c?.messages?.length || 0) === 0)}
      />
      <div className="flex-1 flex flex-col">
        <Header 
          onOpenDocs={() => setIsDocsOpen(true)}
          activeDocName={activeDoc?.pdf_name}
        />
        <ChatWindow messages={currentMessages} isLoading={isLoading} />
        <InputBox onSendMessage={handleSendMessage} onUploadPdf={handleUploadPdf} activeDocName={activeDoc?.pdf_name} disabled={isLoading} onStop={handleStop} uploading={uploading} uploadProgress={uploadProgress} />
      </div>
      
      {isDocsOpen && (
        <DocumentManagerModal
          onClose={() => setIsDocsOpen(false)}
          activeDoc={activeDoc}
          onSelect={(doc) => {
            setActiveDoc(doc);
            setIsDocsOpen(false);
          }}
          refreshKey={docsRefreshKey}
        />
      )}
    </div>
  );
}

export default App;