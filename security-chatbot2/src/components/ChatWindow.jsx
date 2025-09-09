import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

const ChatWindow = ({ messages, isLoading }) => {
  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTo({
        top: chatRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  return (
    <div
      ref={chatRef}
      className="flex-1 overflow-y-auto p-6 bg-dark-slate space-y-6"
    >
      {messages.map((msg, index) => (
        <MessageBubble key={index} sender={msg.sender} text={msg.text} streaming={msg.streaming} />
      ))}
      {isLoading && (
        <MessageBubble sender="bot" text="" streaming={true} />
      )}
    </div>
  );
};

export default ChatWindow;