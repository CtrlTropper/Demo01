import { ShieldCheckIcon, UserCircleIcon } from '@heroicons/react/24/solid';

const Header = ({ isLoggedIn, onOpenLoginModal, onOpenUserModal }) => {
  return (
    <header className="bg-security-gradient text-white p-4 flex items-center justify-between shadow-md animate-glow glass-effect">
      <div className="flex items-center">
        <ShieldCheckIcon className="h-8 w-8 mr-3 text-neon-cyan animate-glow" />
        <h1 className="text-2xl font-bold">Security Chatbot</h1>
      </div>
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
    </header>
  );
};

export default Header;