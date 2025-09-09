import { useEffect, useState } from 'react';

const DocumentManagerModal = ({ onClose, onSelect, activeDoc }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDocs = async () => {
      setLoading(true);
      try {
        const headers = {};
        const token = localStorage.getItem('auth:token');
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const res = await fetch('/api/documents', { headers });
        const data = await res.json();
        setItems(data.items || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-dark-slate rounded-lg shadow-xl w-full max-w-3xl p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl text-white font-semibold">Quản lý tài liệu</h2>
          <button className="text-gray-300 hover:text-white" onClick={onClose}>✕</button>
        </div>
        {loading ? (
          <div className="text-gray-300">Đang tải...</div>
        ) : (
          <div className="max-h-[60vh] overflow-y-auto divide-y divide-gray-700">
            {items.map((it, idx) => (
              <div key={idx} className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">{it.pdf_name}</div>
                  <div className="text-xs text-gray-400">{it.embedded ? 'Đã nhúng' : 'Chưa nhúng'}</div>
                </div>
                <div className="flex items-center gap-2">
                  <a
                    className="px-3 py-1 rounded bg-gray-700 text-white hover:bg-opacity-80"
                    href={`/api/documents/${encodeURIComponent(it.pdf_name)}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Xem
                  </a>
                  <button
                    className={`px-3 py-1 rounded ${activeDoc?.pdf_name === it.pdf_name ? 'bg-primary-blue text-white' : 'bg-gray-700 text-white hover:bg-opacity-80'}`}
                    onClick={() => onSelect({ id: it.id || null, pdf_name: it.pdf_name })}
                  >
                    {activeDoc?.pdf_name === it.pdf_name ? 'Đang chọn' : 'Chọn'}
                  </button>
                </div>
              </div>
            ))}
            {items.length === 0 && (
              <div className="text-gray-300">Không có tài liệu.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentManagerModal;
