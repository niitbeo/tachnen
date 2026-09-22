import { useState, useCallback } from 'react';
import { Layers, Upload, Loader2, Download, Trophy } from 'lucide-react';
import { api } from '../api';

interface CompareResult {
  model: string;
  ten: string;
  duong?: string;
  giay?: number;
  phu?: number;
  loi?: string;
}

interface Props {
  nen: string;
}

export default function CompareView({ nen }: Props) {
  const [comparing, setComparing] = useState(false);
  const [results, setResults] = useState<CompareResult[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const uploadAndCompare = useCallback(async (files: FileList | File[]) => {
    const imageFiles = Array.from(files).filter(f =>
      /\.(jpe?g|png|webp|bmp|tiff?)$/i.test(f.name)
    );
    if (imageFiles.length === 0) return;

    setComparing(true);
    setResults([]);
    try {
      // Upload first file
      const formData = new FormData();
      formData.append('files', imageFiles[0]);
      const upload = await api.uploadFiles(formData);
      if (!upload.thuMuc) return;

      const filePath = `${upload.thuMuc}\\${imageFiles[0].name}`;

      // Run comparison - this calls all 3 models
      const res = await api.compareModels(filePath, nen);
      setResults(res.ketQua || []);
    } catch (e) {
      console.error('Compare failed:', e);
    } finally {
      setComparing(false);
    }
  }, [nen]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) uploadAndCompare(e.dataTransfer.files);
  }, [uploadAndCompare]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) uploadAndCompare(e.target.files);
  }, [uploadAndCompare]);

  const fastest = results.filter(r => r.giay != null).sort((a, b) => (a.giay || 99) - (b.giay || 99))[0]?.model;

  return (
    <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-700/60">
      <h2 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-100">
        <Layers size={18} className="text-purple-400" />
        So sánh 3 Model
      </h2>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-4 text-center transition-all cursor-pointer mb-4
          ${dragOver ? 'border-purple-400 bg-purple-500/10' : 'border-slate-700 hover:border-slate-500 bg-slate-950/50'}
          ${comparing ? 'opacity-60 pointer-events-none' : ''}`}
        onClick={() => document.getElementById('compare-input')?.click()}
      >
        <input id="compare-input" type="file" accept="image/*" className="hidden" onChange={handleFileInput} />
        {comparing ? (
          <div className="flex items-center justify-center gap-2 text-purple-400">
            <Loader2 size={20} className="animate-spin" />
            <span className="text-sm font-medium">Đang chạy 3 model...</span>
          </div>
        ) : (
          <>
            <Upload size={22} className={`mx-auto mb-1 ${dragOver ? 'text-purple-400' : 'text-slate-500'}`} />
            <p className="text-sm text-slate-300">Kéo 1 ảnh vào đây để so sánh</p>
          </>
        )}
      </div>

      {/* Results grid */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {results.map((r) => (
            <div
              key={r.model}
              className={`rounded-xl border overflow-hidden transition-all
                ${r.loi ? 'border-red-500/50 bg-red-950/20' : 'border-slate-700/50 bg-slate-950'}
                ${r.model === fastest ? 'ring-2 ring-yellow-500/40' : ''}`}
            >
              {/* Header */}
              <div className="px-3 py-2 bg-slate-800/80 border-b border-slate-700/50 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-200 truncate">{r.ten.split('—')[0].trim()}</span>
                {r.model === fastest && <Trophy size={14} className="text-yellow-400 shrink-0" />}
              </div>

              {/* Image */}
              {r.duong ? (
                <div
                  className="aspect-[4/5]"
                  style={{
                    backgroundImage: 'linear-gradient(45deg, #1e293b 25%, transparent 25%), linear-gradient(-45deg, #1e293b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #1e293b 75%), linear-gradient(-45deg, transparent 75%, #1e293b 75%)',
                    backgroundSize: '12px 12px',
                    backgroundPosition: '0 0, 0 6px, 6px -6px, -6px 0px',
                    backgroundColor: '#0f172a',
                  }}
                >
                  <img
                    src={api.getImageUrl(r.duong, 400)}
                    alt={r.model}
                    className="w-full h-full object-contain"
                  />
                </div>
              ) : (
                <div className="aspect-[4/5] flex items-center justify-center text-red-400 text-xs p-3">
                  Lỗi: {r.loi}
                </div>
              )}

              {/* Stats */}
              <div className="px-3 py-2 bg-slate-800/50 border-t border-slate-700/50 flex items-center justify-between text-xs">
                <span className="text-slate-400">
                  {r.giay != null && <><span className="text-blue-400 font-bold">{r.giay}s</span> · </>}
                  {r.phu != null && <span>chủ thể {r.phu}%</span>}
                </span>
                {r.duong && (
                  <a href={api.getDownloadUrl(r.duong)} download className="text-blue-400 hover:text-blue-300">
                    <Download size={14} />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
