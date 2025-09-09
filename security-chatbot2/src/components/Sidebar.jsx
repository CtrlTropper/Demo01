import { useState } from 'react';
import { PlusIcon, MagnifyingGlassIcon, PencilIcon, TrashIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/solid';

const Sidebar = ({ isOpen, onToggle, conversations, currentId, onSelect, onNewChat, onDelete, onRename, searchTerm, setSearchTerm }) => {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const startEditing = (id, title) => {
    setEditingId(id);
    setEditTitle(title);
  };

  const saveEdit = (id) => {
    if (editTitle.trim()) {
      onRename(id, editTitle);
    }
    setEditingId(null);
  };

  // Bỏ các chức năng quản trị

  return (
    <div className={`bg-dark-slate text-white flex flex-col shadow-md transition-all duration-300 ${isOpen ? 'w-72' : 'w-12'} glass-effect`}>
      <div className="p-2 flex items-center justify-end border-b border-neon-cyan">
        <button 
          onClick={onToggle}
          className="text-white hover:text-matrix-green transition"
        >
          {isOpen ? <ChevronLeftIcon className="h-6 w-6" /> : <ChevronRightIcon className="h-6 w-6" />}
        </button>
      </div>
      {isOpen && (
        <>
          <div className="p-4 flex items-center border-b border-neon-cyan">
            <button 
              onClick={onNewChat}
              className="flex-1 bg-primary-blue text-white px-4 py-2 rounded-lg hover:bg-opacity-80 transition shadow-soft flex items-center justify-center"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              New Chat
            </button>
          </div>
          <div className="p-4">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-300" />
              <input
                type="text"
                placeholder="Search chats..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full p-2 pl-10 rounded-lg bg-transparent text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple security-border"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto px-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`p-3 mb-2 rounded-lg cursor-pointer hover:bg-purple transition flex items-center justify-between ${
                  conv.id === currentId ? 'bg-orange' : 'bg-transparent'
                }`}
              >
                {editingId === conv.id ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={() => saveEdit(conv.id)}
                    onKeyDown={(e) => e.key === 'Enter' && saveEdit(conv.id)}
                    className="flex-1 bg-transparent text-white border-b border-warning-yellow focus:outline-none"
                    autoFocus
                  />
                ) : (
                  <span onClick={() => onSelect(conv.id)} className="flex-1 truncate">
                    {conv.title}
                  </span>
                )}
                <div className="flex space-x-2">
                  <button onClick={() => startEditing(conv.id, conv.title)} className="text-success-green hover:text-white">
                    <PencilIcon className="h-4 w-4" />
                  </button>
                  <button onClick={() => onDelete(conv.id)} className="text-danger-red hover:text-white">
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          
        </>
      )}
    </div>
  );
};

export default Sidebar;