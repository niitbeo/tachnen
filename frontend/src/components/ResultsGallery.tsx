import { useState } from 'react';
import { Image as ImageIcon, X, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import { api } from '../api';

interface Props {
  results: string[];
  visible: boolean;
}

export default function ResultsGallery({ results, visible }: Props) {
  const [viewIdx, setViewIdx] = useState<number | null>(null);

  if (!visible || results.length === 0) return null;

  const close = () => setViewIdx(null);
  const prev = () => setViewIdx(i => i !== null ? (i - 1 + results.length) % results.length : null);
  const next = () => setViewIdx(i => i !== null ? (i + 1) % results.length : null);

  const fileName = (path: string) => path.split('\\').pop() || path;

  return (
    <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-700/60">
      <h2 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-100">
        <ImageIcon size={18} className="text-emerald-400" />
        Kết quả ({results.length} ảnh)
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {results.map((path, idx) => (
          <div key={idx} className="relative group">
            <div
              onClick={() => setViewIdx(idx)}
              className="aspect-[4/5] rounded-lg overflow-hidden border border-slate-700/50
                         cursor-pointer hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/10 transition-all"
              style={{
                backgroundImage: 'linear-gradient(45deg, #1e293b 25%, transparent 25%), linear-gradient(-45deg, #1e293b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #1e293b 75%), linear-gradient(-45deg, transparent 75%, #1e293b 75%)',
                backgroundSize: '16px 16px',
                backgroundPosition: '0 0, 0 8px, 8px -8px, -8px 0px',
                backgroundColor: '#0f172a',
              }}
              title={fileName(path)}
            >
              <img
                src={api.getImageUrl(path, 300)}
                alt={`Result ${idx + 1}`}
                loading="lazy"
                className="w-full h-full object-contain p-1 group-hover:scale-105 transition-transform duration-200"
              />
            </div>
            {/* Download button */}
            <a
              href={api.getDownloadUrl(path)}
              download={fileName(path)}
              onClick={(e) => e.stopPropagation()}
              className="absolute bottom-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-blue-600 text-white
                         opacity-0 group-hover:opacity-100 transition-all"
              title="Tải ảnh"
            >
              <Download size={14} />
            </a>
          </div>
        ))}
      </div>

      {/* Lightbox */}
      {viewIdx !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center"
          onClick={close}
        >
          <button onClick={close}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors z-10">
            <X size={22} />
          </button>

          <div className="absolute top-5 left-1/2 -translate-x-1/2 text-white/60 text-sm font-mono z-10">
            {viewIdx + 1} / {results.length}
          </div>

          {/* Download in lightbox */}
          <a
            href={api.getDownloadUrl(results[viewIdx])}
            download={fileName(results[viewIdx])}
            onClick={(e) => e.stopPropagation()}
            className="absolute top-4 left-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors z-10"
          >
            <Download size={16} /> Tải ảnh
          </a>

          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/50 text-xs font-mono max-w-[80%] truncate z-10">
            {fileName(results[viewIdx])}
          </div>

          {results.length > 1 && (
            <button onClick={(e) => { e.stopPropagation(); prev(); }}
              className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors z-10">
              <ChevronLeft size={28} />
            </button>
          )}

          {results.length > 1 && (
            <button onClick={(e) => { e.stopPropagation(); next(); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors z-10">
              <ChevronRight size={28} />
            </button>
          )}

          <img
            src={api.getImageUrl(results[viewIdx], 1200)}
            alt=""
            onClick={(e) => e.stopPropagation()}
            className="max-w-[90vw] max-h-[85vh] object-contain rounded-lg shadow-2xl"
            style={{
              backgroundImage: 'linear-gradient(45deg, #334155 25%, transparent 25%), linear-gradient(-45deg, #334155 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #334155 75%), linear-gradient(-45deg, transparent 75%, #334155 75%)',
              backgroundSize: '20px 20px',
              backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px',
              backgroundColor: '#1e293b',
            }}
          />
        </div>
      )}
    </div>
  );
}
