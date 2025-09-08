import { useEffect, useState } from 'react';

const UserModal = ({ user, onClose, onLogout }) => {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const token = localStorage.getItem('auth:token');
        const res = await fetch('/api/auth/me', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        const data = await res.json();
        if (!data.authenticated) {
          setError('Bạn chưa đăng nhập.');
        } else {
          setInfo(data);
        }
      } catch (e) {
        setError('Không thể tải thông tin người dùng.');
      }
    };
    fetchMe();
  }, []);

  const handleEdit = () => {
    alert('Chỉnh sửa thông tin người dùng');
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-dark-slate text-white p-6 rounded-lg shadow-lg w-80 relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-300 hover:text-white">×</button>
        <h2 className="text-xl font-bold mb-4">Thông tin người dùng</h2>
        {error ? (
          <p className="text-danger-red">{error}</p>
        ) : (
          <>
            <p><strong>Username:</strong> {info?.username || user.name}</p>
            <p><strong>Role:</strong> {info?.role || (user.isAdmin ? 'admin' : 'user')}</p>
            <p className="text-sm text-gray-300 mt-2">ID: {info?.id}</p>
            <p className="text-sm text-gray-300">Created: {info?.created_at}</p>
          </>
        )}
        <div className="mt-6 flex justify-between">
          <button
            onClick={handleEdit}
            className="bg-primary-blue text-white px-4 py-2 rounded-lg hover:bg-opacity-80 transition"
          >
            Chỉnh sửa
          </button>
          <button
            onClick={onLogout}
            className="bg-danger-red text-white px-4 py-2 rounded-lg hover:bg-opacity-80 transition"
          >
            Đăng xuất
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserModal;