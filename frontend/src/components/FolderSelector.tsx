import { useState, useCallback } from 'react';
import { Upload, FolderOpen, X, Image as ImageIcon } from 'lucide-react';
import { api } from '../api';
import FolderBrowser from './FolderBrowser';

interface Props {
  folder: string;
  imageCount: number;
  recursive: boolean;
  onFolderChange: (f: string) => void;
  onRecursiveChange: (r: boolean) => void;
  onImageCountChange: (c: number) => void;
}

export default function FolderSelector({ folder, imageCount, recursive, onFolderChange, onRecursiveChange, onImageCountChange }: Props) {
  const [showBrowser, setShowBrowser] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [fileNames, setFileNames] = useState<string[]>([]);

  // Upload files to server
  const uploadFiles = useCallback(async (files: FileList | File[]) => {
    const imageFiles = Array.from(files).filter(f =>
      /\.(jpe?g|png|webp|bmp|tiff?)$/i.test(f.name)
    );
    if (imageFiles.length === 0) return;

    setUploading(true);
    try {
      const formData = new FormData();
      for (const f of imageFiles) {
        formData.append('files', f);
      }
      const res = await api.uploadFiles(formData);
      if (res.thuMuc) {
        onFolderChange(res.thuMuc);
        onImageCountChange(res.so || imageFiles.length);
        setFileNames(imageFiles.map(f => f.name));
      }
    } catch (e) {
      console.error('Upload failed:', e);
    } finally {
      setUploading(false);
    }
  }, [onFolderChange, onImageCountChange]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      uploadFiles(e.dataTransfer.files);
    }
  }, [uploadFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadFiles(e.target.files);
    }
  }, [uploadFiles]);

  const handleBrowseFolder = async () => {
    const res = await api.openFolderDialog('Chọn thư mục chứa ảnh', folder, recursive);
    if (res?.fallback) {
      setShowBrowser(true);
    } else if (res?.duong) {
      onFolderChange(res.duong);
      onImageCountChange(res.so ?? 0);
      setFileNames([]);
    }
  };

  const clearSelection = () => {
    onFolderChange('');
    onImageCountChange(0);
    setFileNames([]);
  };

  return (
    <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-700/60">
      <h2 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-100">
        <ImageIcon size={18} className="text-blue-400" />
        Ảnh cần tách
      </h2>

      {/* Drag & Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer
          ${dragOver
            ? 'border-blue-400 bg-blue-500/10'
            : 'border-slate-700 hover:border-slate-500 bg-slate-950/50'
          }
          ${uploading ? 'opacity-60 pointer-events-none' : ''}
        `}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept="image/*"
          className="hidden"
          onChange={handleFileInput}
        />
        <Upload size={28} className={`mx-auto mb-2 ${dragOver ? 'text-blue-400' : 'text-slate-500'}`} />
        <p className="text-sm text-slate-300 font-medium">
          {uploading ? 'Đang tải lên...' : 'Kéo thả ảnh vào đây'}
        </p>
        <p className="text-xs text-slate-500 mt-1">
          hoặc bấm để chọn ảnh · JPG, PNG, WebP, BMP
        </p>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-3 my-3">
        <div className="flex-1 h-px bg-slate-700/60" />
        <span className="text-xs text-slate-500">hoặc</span>
        <div className="flex-1 h-px bg-slate-700/60" />
      </div>

      {/* Folder browse button */}
      <button
        onClick={handleBrowseFolder}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm
                   bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
      >
        <FolderOpen size={16} />
        Chọn thư mục trên máy
      </button>

      {/* Selected info */}
      {(folder || fileNames.length > 0) && (
        <div className="mt-3 p-3 bg-slate-950 rounded-lg border border-slate-700/50 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            {fileNames.length > 0 ? (
              <p className="text-sm text-slate-300 truncate">
                <span className="text-emerald-400 font-bold">{fileNames.length}</span> ảnh đã chọn
              </p>
            ) : (
              <>
                <p className="text-xs text-slate-500 truncate font-mono">{folder}</p>
                <p className="text-sm text-slate-300 mt-0.5">
                  <span className="text-emerald-400 font-bold">{imageCount}</span> ảnh
                </p>
              </>
            )}
          </div>
          <button onClick={clearSelection} className="p-1 hover:bg-slate-800 rounded text-slate-500">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Recursive checkbox (only for folder mode) */}
      {folder && fileNames.length === 0 && (
        <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-400 mt-3">
          <input
            type="checkbox"
            checked={recursive}
            onChange={async (e) => {
              onRecursiveChange(e.target.checked);
              if (folder) {
                const count = await api.countImages(folder, e.target.checked);
                onImageCountChange(count);
              }
            }}
            className="rounded accent-blue-500"
          />
          Gồm cả thư mục con
        </label>
      )}

      <FolderBrowser
        open={showBrowser}
        initialPath={folder || ''}
        onSelect={(path, count) => {
          onFolderChange(path);
          onImageCountChange(count);
          setFileNames([]);
          setShowBrowser(false);
        }}
        onClose={() => setShowBrowser(false)}
      />
    </div>
  );
}
