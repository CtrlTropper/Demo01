import { UserIcon, CpuChipIcon, ClipboardIcon, CheckIcon } from '@heroicons/react/24/solid';
import { useState } from 'react';

const MessageBubble = ({ sender, text, streaming = false }) => {
  const isUser = sender === 'user';
  const [copied, setCopied] = useState(false);
  const containsDoneToken = !!(text && text.includes('[DONE]'));
  const displayText = (text || '').replaceAll('[DONE]', '').trimEnd();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  };
  return (
    <div className={`flex items-start ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <CpuChipIcon className="h-8 w-8 text-matrix-green mr-2 flex-shrink-0" />
      )}
      <div className="flex flex-col items-start">
        <div
          className={`message-bubble shadow-soft transition-opacity duration-500 opacity-0 animate-slide-up whitespace-pre-wrap break-words relative max-w-[80%] px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-primary-blue text-white'
              : 'glass-effect text-white'
          }`}
        >
          {displayText || (streaming ? (
            <span className="inline-flex items-center">
              <span className="mr-2">Đang tạo câu trả lời</span>
              <span className="inline-flex">
                <span className="w-2 h-2 bg-neon-cyan rounded-full animate-bounce mr-1" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-neon-cyan rounded-full animate-bounce mr-1" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-neon-cyan rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </span>
            </span>
          ) : null)}
          {!streaming && !isUser && (displayText || containsDoneToken) && (
            <div className="absolute -top-3 -right-3 flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="bg-gray-700/80 hover:bg-gray-700 text-white p-1 rounded shadow-soft"
                title="Sao chép"
              >
                {copied ? <CheckIcon className="h-4 w-4 text-matrix-green" /> : <ClipboardIcon className="h-4 w-4" />}
              </button>
            </div>
          )}
        </div>
        {!streaming && !isUser && containsDoneToken && (
          <div className="mt-1 inline-flex items-center text-xs text-gray-400">
            <CheckIcon className="h-3 w-3 text-matrix-green mr-1" /> Hoàn tất
          </div>
        )}
      </div>
      {isUser && (
        <UserIcon className="h-8 w-8 text-neon-cyan ml-2 flex-shrink-0" />
      )}
    </div>
  );
};

export default MessageBubble;