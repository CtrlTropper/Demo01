import { useEffect, useRef, useState } from 'react';
import { PaperAirplaneIcon, ArrowUpTrayIcon, StopIcon } from '@heroicons/react/24/solid';

const InputBox = ({ onSendMessage, onUploadPdf, activeDocName, disabled = false, onStop, uploading = false, uploadProgress = 0 }) => {
  const [input, setInput] = useState('');
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  const handleSend = () => {
    if (disabled) return;
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = 'auto';
    textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
  }, [input]);

  const handleChooseFile = () => {
    if (disabled) return;
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Vui lòng chọn tệp PDF.');
      e.target.value = '';
      return;
    }
    if (onUploadPdf) onUploadPdf(file);
    e.target.value = '';
  };

  return (
    <div className="bg-dark-slate p-4 shadow-md">
      <div className="flex items-center">
        <button
          onClick={handleChooseFile}
          className={`bg-gray-700 text-white p-3 rounded-l-xl hover:bg-opacity-80 transition shadow-soft ${disabled ? 'opacity-60 cursor-not-allowed hover:bg-opacity-100' : ''}`}
          disabled={disabled}
          title="Tải lên PDF"
        >
          <ArrowUpTrayIcon className="h-6 w-6" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={handleFileChange}
        />
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Nhập câu hỏi... (Shift+Enter để xuống dòng)"
          className={`flex-1 p-3 bg-dark-slate text-white placeholder-gray-400 border-none focus:outline-none focus:ring-2 focus:ring-neon-cyan transition glass-effect resize-none ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
          style={{ borderTopLeftRadius: 0, borderBottomLeftRadius: 0 }}
          rows={1}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={disabled}
        />
        {disabled ? (
          <button
            onClick={onStop}
            className={`bg-warning-yellow text-black p-3 rounded-r-xl hover:bg-opacity-80 transition shadow-soft ${disabled ? '' : 'opacity-60 cursor-not-allowed'}`}
            title="Dừng sinh"
          >
            <StopIcon className="h-6 w-6" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            className={`bg-primary-blue text-white p-3 rounded-r-xl hover:bg-opacity-80 transition shadow-soft animate-glow ${disabled ? 'opacity-60 cursor-not-allowed hover:bg-opacity-100' : ''}`}
            disabled={disabled}
          >
            <PaperAirplaneIcon className="h-6 w-6" />
          </button>
        )}
      </div>
      {uploading && (
        <div className="mt-2">
          <div className="h-2 w-full bg-gray-700 rounded">
            <div className="h-2 bg-primary-blue rounded" style={{ width: `${Math.max(0, Math.min(100, uploadProgress))}%` }} />
          </div>
          <div className="text-xs text-gray-400 mt-1">Đang tải lên... {Math.floor(Math.max(0, Math.min(100, uploadProgress)))}%</div>
        </div>
      )}
      {activeDocName ? (
        <div className="mt-2 text-xs text-gray-400">Đang tập trung vào: {activeDocName}</div>
      ) : null}
    </div>
  );
};

export default InputBox;