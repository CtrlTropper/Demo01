import { useState } from 'react';
import { User, Lock, Eye, EyeOff, Loader2 } from 'lucide-react';

const LoginModal = ({ onClose, onLogin }) => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [errors, setErrors] = useState({ username: '', password: '', general: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [isLocked, setIsLocked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    validateField(name, value);
  };

  const validateField = (name, value) => {
    let error = '';
    if (name === 'username' && !value.trim()) {
      error = 'Username is required';
    }
    if (name === 'password' && !value.trim()) {
      error = 'Password is required';
    }
    setErrors((prev) => ({ ...prev, [name]: error }));
  };

  const simulateLogin = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));

    if (formData.username === 'admin' && formData.password === 'password123') {
      setAttempts(0);
      onLogin();
    } else {
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);
      setErrors((prev) => ({ ...prev, general: 'Invalid credentials' }));
      if (newAttempts >= 5) {
        setIsLocked(true);
        setErrors((prev) => ({ ...prev, general: 'Account locked. Contact support.' }));
      }
    }
    setIsLoading(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLocked || isLoading) return;
    if (!formData.username || !formData.password) {
      validateField('username', formData.username);
      validateField('password', formData.password);
      return;
    }
    simulateLogin();
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-dark-slate text-white p-8 rounded-xl shadow-lg w-full max-w-md glass-effect">
        <h2 className="text-2xl font-bold mb-6 text-center">Đăng nhập</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block mb-1">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-300" />
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className="w-full p-3 pl-10 rounded-lg bg-transparent border border-gray-500 focus:border-primary-blue focus:outline-none transition"
                placeholder="Enter username"
                disabled={isLocked || isLoading}
              />
            </div>
            {errors.username && <p className="text-danger-red mt-1">{errors.username}</p>}
          </div>
          <div className="mb-4">
            <label className="block mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-300" />
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full p-3 pl-10 pr-10 rounded-lg bg-transparent border border-gray-500 focus:border-primary-blue focus:outline-none transition"
                placeholder="Enter password"
                disabled={isLocked || isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-300"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {errors.password && <p className="text-danger-red mt-1">{errors.password}</p>}
          </div>
          <div className="flex items-center justify-between mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="mr-2"
                disabled={isLocked || isLoading}
              />
              Remember me
            </label>
            <a href="#" className="text-primary-blue hover:underline" onClick={(e) => { e.preventDefault(); alert('Forgot password?'); }}>
              Forgot password?
            </a>
          </div>
          {errors.general && <p className="text-danger-red mb-4 text-center">{errors.general}</p>}
          <button
            type="submit"
            className="w-full bg-primary-blue text-white py-3 rounded-lg hover:bg-opacity-80 transition flex items-center justify-center disabled:opacity-50"
            disabled={isLocked || isLoading}
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : null}
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <div className="mt-6 text-center">
          <p className="mb-2">Demo credentials:</p>
          <p className="text-gray-300">Username: admin</p>
          <p className="text-gray-300">Password: password123</p>
        </div>
        <p className="text-center text-gray-300 mt-4">Protected by SSL encryption 🔒</p>
      </div>
    </div>
  );
};

export default LoginModal;