const UserModal = ({ user, onClose, onLogout }) => {
  const handleEdit = () => {
    alert('Chỉnh sửa thông tin người dùng');
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-dark-slate text-white p-6 rounded-lg shadow-lg w-80">
        <h2 className="text-xl font-bold mb-4">Thông tin người dùng</h2>
        <p><strong>Tên:</strong> {user.name}</p>
        <p><strong>Chức vụ:</strong> {user.position}</p>
        <p><strong>Đơn vị:</strong> {user.unit}</p>
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