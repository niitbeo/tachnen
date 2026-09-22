import { useState, useEffect } from 'react';
import { FolderOpen, ChevronUp, X } from 'lucide-react';
import { api } from '../api';

interface Props {
  open: boolean;
  initialPath: string;
  onSelect: (path: string, count: number) => void;
  onClose: () => void;
}

export default function FolderBrowser({ open, initialPath, onSelect, onClose }: Props) {
  const [currentPath, setCurrentPath] = useState('');
  const [parentPath, setParentPath] = useState('');
  const [folders, setFolders] = useState<string[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) loadDir(initialPath || '');
  }, [open, initialPath]);

  const loadDir = async (path: string) => {
    setLoading(true);
    try {
      const res = await api.listDir(path);
      setCurrentPath(res.duong);
      setParentPath(res.cha);
      setFolders(res.thuMuc);
      setCount(res.soAnh);
    } catch {
      // fallback to root
      const res = await api.listDir('');
      setCurrentPath(res.duong);
      setParentPath(res.cha);
      setFolders(res.thuMuc);
      setCount(res.soAnh);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  const folderName = (path: string) => {
    const parts = path.replace(/\\$/, '').split('\\');
    return parts[parts.length - 1] || path;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 rounded-xl border border-slate-700 shadow-2xl w-full max-w-xl overflow-hidden flex flex-col max-h-[75vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700/60">
          <h3 className="font-semibold flex items-center gap-2">
            <FolderOpen size={18} className="text-blue-400" />
            Chọn thư mục chứa ảnh
          </h3>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors text-slate-400">
            <X size={18} />
          </button>
        </div>

        {/* Breadcrumb */}
        <div className="px-5 py-3 bg-slate-950 border-b border-slate-700/60 flex items-center gap-2 text-sm">
          <button
            onClick={() => parentPath !== undefined && loadDir(parentPath)}
            disabled={!currentPath || loading}
            className="p-1 hover:bg-slate-700 rounded transition-colors text-slate-400 disabled:opacity-30"
            title="Lên trên"
          >
            <ChevronUp size={16} />
          </button>
          <span className="font-mono text-slate-300 truncate">
            {currentPath || 'Máy tính'}
          </span>
        </div>

        {/* Folder list */}
        <div className="flex-1 overflow-y-auto p-2 min-h-[200px]">
          {loading ? (
            <div className="text-center py-8 text-slate-500 text-sm">Đang tải…</div>
          ) : folders.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm">(Không có thư mục con)</div>
          ) : (
            folders.map((f) => (
              <button
                key={f}
                onClick={() => loadDir(f)}
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-800 flex items-center gap-3 group transition-colors"
              >
                <FolderOpen size={16} className="text-blue-400/60 group-hover:text-blue-400 shrink-0" />
                <span className="text-sm text-slate-200 truncate">{folderName(f)}</span>
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-700/60 flex items-center justify-between">
          <span className="text-sm text-slate-400">
            {currentPath && (
              <><span className="text-emerald-400 font-medium">{count}</span> ảnh tìm thấy</>
            )}
          </span>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors">
              Huỷ
            </button>
            <button
              onClick={() => currentPath && onSelect(currentPath, count)}
              disabled={!currentPath}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-500 disabled:opacity-40 transition-colors text-white"
            >
              Chọn thư mục này
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
