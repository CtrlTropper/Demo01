import { ShieldCheckIcon, UserCircleIcon, DocumentTextIcon } from '@heroicons/react/24/solid';

const Header = ({ isLoggedIn, onOpenLoginModal, onOpenUserModal, onOpenDocs }) => {
  return (
    <header className="bg-security-gradient text-white p-4 flex items-center justify-between shadow-md animate-glow glass-effect">
      <div className="flex items-center">
        <ShieldCheckIcon className="h-8 w-8 mr-3 text-neon-cyan animate-glow" />
        <h1 className="text-2xl font-bold">Security Chatbot</h1>
      </div>
      <div className="flex items-center gap-4">
        <button
          onClick={onOpenDocs}
          className="bg-gray-700 text-white px-3 py-2 rounded-lg hover:bg-opacity-80 transition shadow-soft flex items-center gap-2"
        >
          <DocumentTextIcon className="h-5 w-5" />
          Tài liệu
        </button>
        {isLoggedIn ? (
          <UserCircleIcon 
            onClick={onOpenUserModal}
            className="h-8 w-8 cursor-pointer text-white hover:text-neon-cyan transition"
          />
        ) : (
          <button
            onClick={onOpenLoginModal}
            className="bg-primary-blue text-white px-4 py-2 rounded-lg hover:bg-opacity-80 transition shadow-soft"
          >
            Đăng nhập
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;