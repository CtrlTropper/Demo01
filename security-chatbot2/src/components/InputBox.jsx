import { useState } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

const InputBox = ({ onSendMessage }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="bg-dark-slate p-4 flex items-center shadow-md">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Nhập câu hỏi..."
        className="flex-1 p-3 rounded-l-xl bg-dark-slate text-white placeholder-gray-400 border-none focus:outline-none focus:ring-2 focus:ring-neon-cyan transition glass-effect"
        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
      />
      <button
        onClick={handleSend}
        className="bg-primary-blue text-white p-3 rounded-r-xl hover:bg-opacity-80 transition shadow-soft animate-glow"
      >
        <PaperAirplaneIcon className="h-6 w-6" />
      </button>
    </div>
  );
};

export default InputBox;