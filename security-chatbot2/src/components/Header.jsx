import { ShieldCheckIcon, UserCircleIcon } from '@heroicons/react/24/solid';

const Header = ({ onOpenModal }) => {
  return (
    <header className="bg-security-gradient text-white p-4 flex items-center justify-between shadow-md animate-glow glass-effect">
      <div className="flex items-center">
        <ShieldCheckIcon className="h-8 w-8 mr-3 text-neon-cyan animate-glow" />
        <h1 className="text-2xl font-bold">Security Chatbot</h1>
      </div>
      <UserCircleIcon 
        onClick={onOpenModal}
        className="h-8 w-8 cursor-pointer text-white hover:text-neon-cyan transition"
      />
    </header>
  );
};

export default Header;