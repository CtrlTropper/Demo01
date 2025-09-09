import { UserIcon, CpuChipIcon } from '@heroicons/react/24/solid';

const MessageBubble = ({ sender, text, streaming = false }) => {
  const isUser = sender === 'user';
  return (
    <div className={`flex items-start ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <CpuChipIcon className="h-8 w-8 text-matrix-green mr-2 flex-shrink-0" />
      )}
      <div
        className={`message-bubble shadow-soft transition-opacity duration-500 opacity-0 animate-slide-up whitespace-pre-wrap ${
          isUser
            ? 'bg-message-gradient text-white'
            : 'glass-effect text-white'
        }`}
      >
        {text || (streaming ? (
          <span className="inline-flex items-center">
            <span className="mr-2">Đang tạo câu trả lời</span>
            <span className="inline-flex">
              <span className="w-2 h-2 bg-neon-cyan rounded-full animate-bounce mr-1" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-neon-cyan rounded-full animate-bounce mr-1" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-neon-cyan rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </span>
          </span>
        ) : null)}
        {!streaming && !isUser && text && (
          <span className="ml-2 text-xs text-gray-300 align-baseline">• đã xong</span>
        )}
      </div>
      {isUser && (
        <UserIcon className="h-8 w-8 text-neon-cyan ml-2 flex-shrink-0" />
      )}
    </div>
  );
};

export default MessageBubble;