import { useEffect, useRef, useState } from 'react';

const DocumentManagerModal = ({ onClose, onSelect, activeDoc, refreshKey = 0 }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState('');
  const timersRef = useRef({}); // key -> interval id

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
  }, [refreshKey]);

  const buildViewHref = (it) => {
    const base = `/api/documents/${encodeURIComponent(it.pdf_name)}`;
    if (it.category && it.category !== 'Uploads' && it.category !== 'Initial') {
      return `${base}?category=${encodeURIComponent(it.category)}`;
    }
    return base;
  };

  const handleEmbed = async (it) => {
    const key = `${it.pdf_name}|${it.category || ''}`;
    // Bật trạng thái embedding và khởi động tiến độ giả lập
    setItems(prev => prev.map(p => (
      p.pdf_name === it.pdf_name && p.category === it.category
        ? { ...p, embedding: true, progress: 5 }
        : p
    )));
    timersRef.current[key] = setInterval(() => {
      setItems(prev => prev.map(p => {
        if (p.pdf_name === it.pdf_name && p.category === it.category) {
          const next = Math.min(90, (p.progress || 0) + 5);
          return { ...p, progress: next };
        }
        return p;
      }));
    }, 300);

    try {
      let url = `/api/documents/${encodeURIComponent(it.pdf_name)}/embed`;
      if (it.category && it.category !== 'Uploads' && it.category !== 'Initial') {
        url += `?category=${encodeURIComponent(it.category)}`;
      }
      const res = await fetch(url, { method: 'POST' });
      if (res.ok) {
        // Hoàn tất: đặt 100% và chuyển sang Đã nhúng
        setItems(prev => prev.map(p => (
          p.pdf_name === it.pdf_name && p.category === it.category
            ? { ...p, embedded: true, embedding: false, progress: 100 }
            : p
        )));
      } else {
        // Lỗi: tắt embedding
        setItems(prev => prev.map(p => (
          p.pdf_name === it.pdf_name && p.category === it.category
            ? { ...p, embedding: false }
            : p
        )));
      }
    } catch (e) {
      console.error(e);
      setItems(prev => prev.map(p => (
        p.pdf_name === it.pdf_name && p.category === it.category
          ? { ...p, embedding: false }
          : p
      )));
    } finally {
      if (timersRef.current[key]) {
        clearInterval(timersRef.current[key]);
        delete timersRef.current[key];
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-dark-slate rounded-lg shadow-xl w-full max-w-2xl p-4">
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
          <div className="max-h-[60vh] overflow-y-auto overflow-x-hidden">
            <table className="w-full text-left text-sm table-fixed">
              <colgroup>
                <col style={{ width: '65%' }} />
                <col style={{ width: '35%' }} />
              </colgroup>
              <thead className="sticky top-0 bg-gray-800 text-gray-300">
                <tr>
                  <th className="px-3 py-2 font-medium">Tên tài liệu</th>
                  <th className="px-3 py-2 font-medium">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {items.filter(it => it.pdf_name.toLowerCase().includes(q.toLowerCase())).map((it, idx) => (
                  <tr key={`${it.pdf_name}-${it.category || 'NA'}-${idx}`}>
                    <td className="px-3 py-3 align-top">
                      <div className="text-white font-medium truncate" title={it.pdf_name}>{it.pdf_name}</div>
                      <div className="text-xs text-gray-400">{it.embedded ? 'Đã nhúng' : 'Chưa nhúng'} · Nguồn: {it.category || 'Initial'}</div>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <a
                          className="px-3 py-1 rounded bg-gray-700 text-white hover:bg-opacity-80"
                          href={buildViewHref(it)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Xem
                        </a>
                        {!it.embedded ? (
                          it.embedding ? (
                            <div className="w-32">
                              <div className="h-2 w-full bg-gray-700 rounded">
                                <div className="h-2 bg-primary-blue rounded" style={{ width: `${it.progress || 0}%` }} />
                              </div>
                              <div className="text-xs text-gray-400 mt-1">Đang nhúng... {Math.floor(it.progress || 0)}%</div>
                            </div>
                          ) : (
                            <button
                              className="px-3 py-1 rounded bg-primary-blue text-white hover:bg-opacity-80"
                              onClick={() => handleEmbed(it)}
                            >
                              Nhúng
                            </button>
                          )
                        ) : (
                          <span className="px-3 py-1 rounded bg-emerald-700 text-white text-sm">Đã nhúng</span>
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
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={2} className="px-3 py-4 text-gray-300">Không có tài liệu.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentManagerModal;
