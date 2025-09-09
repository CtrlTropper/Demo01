import { useEffect, useState } from 'react';

const DocumentManagerModal = ({ onClose, onSelect, activeDoc }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState('');

  useEffect(() => {
    const fetchDocs = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/documents');
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

  const buildViewHref = (it) => {
    const base = `/api/documents/${encodeURIComponent(it.pdf_name)}`;
    if (it.category && it.category !== 'Uploads' && it.category !== 'Initial') {
      return `${base}?category=${encodeURIComponent(it.category)}`;
    }
    return base;
  };

  const handleEmbed = async (it) => {
    try {
      let url = `/api/documents/${encodeURIComponent(it.pdf_name)}/embed`;
      if (it.category && it.category !== 'Uploads' && it.category !== 'Initial') {
        url += `?category=${encodeURIComponent(it.category)}`;
      }
      const res = await fetch(url, { method: 'POST' });
      if (res.ok) {
        setItems(prev => prev.map(p => p.pdf_name === it.pdf_name && p.category === it.category ? { ...p, embedded: true } : p));
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-dark-slate rounded-lg shadow-xl w-full max-w-3xl p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl text-white font-semibold">Quản lý tài liệu</h2>
          <button className="text-gray-300 hover:text-white" onClick={onClose}>✕</button>
        </div>
        <div className="mb-3 flex items-center gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm theo tên tài liệu..."
            className="w-full px-3 py-2 rounded bg-gray-800 text-white placeholder-gray-400 focus:outline-none"
          />
        </div>
        {loading ? (
          <div className="text-gray-300">Đang tải...</div>
        ) : (
          <div className="max-h-[60vh] overflow-y-auto divide-y divide-gray-700">
            {items.filter(it => it.pdf_name.toLowerCase().includes(q.toLowerCase())).map((it, idx) => (
              <div key={`${it.pdf_name}-${it.category || 'NA'}-${idx}`} className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">{it.pdf_name}</div>
                  <div className="text-xs text-gray-400">{it.embedded ? 'Đã nhúng' : 'Chưa nhúng'} · Nguồn: {it.category || 'Initial'}</div>
                </div>
                <div className="flex items-center gap-2">
                  <a
                    className="px-3 py-1 rounded bg-gray-700 text-white hover:bg-opacity-80"
                    href={buildViewHref(it)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Xem
                  </a>
                  {!it.embedded && (
                    <button
                      className="px-3 py-1 rounded bg-primary-blue text-white hover:bg-opacity-80"
                      onClick={() => handleEmbed(it)}
                    >
                      Nhúng
                    </button>
                  )}
                  <button
                    className={`px-3 py-1 rounded ${activeDoc?.pdf_name === it.pdf_name ? 'bg-primary-blue text-white' : 'bg-gray-700 text-white hover:bg-opacity-80'}`}
                    onClick={() => onSelect({ id: it.id || null, pdf_name: it.pdf_name })}
                  >
                    {activeDoc?.pdf_name === it.pdf_name ? 'Đang chọn' : 'Chọn'}
                  </button>
                  {activeDoc?.pdf_name === it.pdf_name && (
                    <button
                      className="px-3 py-1 rounded bg-gray-600 text-white hover:bg-opacity-80"
                      onClick={() => onSelect(null)}
                    >
                      Bỏ chọn
                    </button>
                  )}
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
