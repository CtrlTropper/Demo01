import { UserIcon, CpuChipIcon } from '@heroicons/react/24/solid';

const MessageBubble = ({ sender, text }) => {
  const isUser = sender === 'user';
  return (
    <div className={`flex items-start ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <CpuChipIcon className="h-8 w-8 text-matrix-green mr-2 flex-shrink-0" />
      )}
      <div
        className={`message-bubble shadow-soft transition-opacity duration-500 opacity-0 animate-slide-up ${
          isUser
            ? 'bg-message-gradient text-white'
            : 'glass-effect text-white'
        }`}
      >
        {text}
      </div>
      {isUser && (
        <UserIcon className="h-8 w-8 text-neon-cyan ml-2 flex-shrink-0" />
      )}
    </div>
  );
};

export default MessageBubble;