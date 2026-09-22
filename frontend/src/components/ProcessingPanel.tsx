import { useRef, useEffect } from 'react';
import { Play, Square, FolderOutput, Monitor } from 'lucide-react';
import type { Progress } from '../types';

interface Props {
  isProcessing: boolean;
  progress: Progress | null;
  folderSelected: boolean;
  onStart: () => void;
  onStop: () => void;
  onOpenFolder: () => void;
}

function formatTime(s: number): string {
  s = Math.round(s);
  if (s < 60) return `${s} giây`;
  return `${Math.floor(s / 60)} phút ${String(s % 60).padStart(2, '0')} giây`;
}

export default function ProcessingPanel({ isProcessing, progress, folderSelected, onStart, onStop, onOpenFolder }: Props) {
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [progress?.nhatKy?.length]);

  const done = (progress?.xong ?? 0) + (progress?.loi ?? 0);
  const total = progress?.tong ?? 0;
  const percentage = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-700/60 flex flex-col">
      {/* Buttons */}
      <div className="flex flex-wrap gap-3 mb-5">
        <button
          onClick={onStart}
          disabled={!folderSelected || isProcessing}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg font-semibold text-sm transition-all
                     disabled:opacity-40 disabled:cursor-not-allowed
                     bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400
                     text-white shadow-lg shadow-blue-500/20"
        >
          <Play size={16} /> Bắt đầu tách nền
        </button>

        <button
          onClick={onStop}
          disabled={!isProcessing}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-all
                     disabled:opacity-40 disabled:cursor-not-allowed
                     bg-slate-800 hover:bg-red-500/20 hover:text-red-400 border border-slate-700 text-slate-300"
        >
          <Square size={16} /> Dừng
        </button>

        <button
          onClick={onOpenFolder}
          disabled={!progress?.thuMucRa && !progress?.daXong}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-all
                     disabled:opacity-40 disabled:cursor-not-allowed
                     bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 ml-auto"
        >
          <FolderOutput size={16} /> Mở kết quả
        </button>
      </div>

      {/* Progress bar */}
      <div className="mb-4 bg-slate-950 p-4 rounded-lg border border-slate-700/50">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-slate-300">
            {progress?.daXong
              ? `✓ Xong ${progress.xong} ảnh` + (progress.loi ? ` · ${progress.loi} lỗi` : '')
              : progress?.dangChay
                ? `Đang xử lý: ${progress.hienTai}`
                : 'Sẵn sàng.'}
          </span>
          <span className="text-emerald-400 font-mono text-xs">
            {total > 0 ? `${done}/${total} · ${percentage}%` : ''}
          </span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ease-out rounded-full ${
              progress?.daXong ? 'bg-emerald-500' : 'bg-gradient-to-r from-blue-500 to-blue-400'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {progress?.dangChay && (
          <div className="mt-2 flex justify-between text-xs text-slate-500 font-mono">
            <span>{formatTime(progress.giay)}</span>
            <span>{progress.con > 1 ? `còn ~${formatTime(progress.con)}` : ''}</span>
          </div>
        )}
      </div>

      {/* Log terminal */}
      <div className="flex-1 flex flex-col bg-slate-950 rounded-lg border border-slate-700/50 overflow-hidden min-h-[200px]">
        <div className="px-3 py-2 bg-slate-900/80 border-b border-slate-800 text-xs font-medium text-slate-500 flex items-center gap-2">
          <Monitor size={13} /> Nhật ký
        </div>
        <div className="flex-1 p-3 overflow-y-auto font-mono text-xs leading-relaxed text-slate-400 max-h-[280px]">
          {progress?.nhatKy?.map((line: string, i: number) => (
            <div key={i} className={line.includes('LỖI') ? 'text-red-400' : line.includes('→') ? 'text-slate-300' : ''}>
              {line}
            </div>
          ))}
          {(!progress?.nhatKy || progress.nhatKy.length === 0) && (
            <div className="text-slate-600 italic">Sẵn sàng.</div>
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}
