import { useState } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

const InputBox = ({ onSendMessage, disabled = false }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (disabled) return;
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="bg-dark-slate p-4 flex items-center shadow-md">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Nhập câu hỏi... (Shift+Enter để xuống dòng)"
        className={`flex-1 p-3 rounded-l-xl bg-dark-slate text-white placeholder-gray-400 border-none focus:outline-none focus:ring-2 focus:ring-neon-cyan transition glass-effect resize-none ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
        rows={1}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        disabled={disabled}
      />
      <button
        onClick={handleSend}
        className={`bg-primary-blue text-white p-3 rounded-r-xl hover:bg-opacity-80 transition shadow-soft animate-glow ${disabled ? 'opacity-60 cursor-not-allowed hover:bg-opacity-100' : ''}`}
        disabled={disabled}
      >
        <PaperAirplaneIcon className="h-6 w-6" />
      </button>
    </div>
  );
};

export default InputBox;