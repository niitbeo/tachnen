import { useState, useEffect, useCallback } from 'react';
import FolderSelector from './components/FolderSelector';
import Settings from './components/Settings';
import ProcessingPanel from './components/ProcessingPanel';
import ResultsGallery from './components/ResultsGallery';
import CompareView from './components/CompareView';
import { api } from './api';
import type { Progress, AppSettings } from './types';

export default function App() {
  const [folder, setFolder] = useState('');
  const [imageCount, setImageCount] = useState(0);
  const [recursive, setRecursive] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [results, setResults] = useState<string[]>([]);
  const [settings, setSettings] = useState<AppSettings>({
    nen: 'trong',
    chatLuong: 2500,
    thuMucRa: '',
    mask: false,
    mauTuChon: '#2f7fd8',
    model: 'hmhcv1',
  });

  // Poll progress while processing
  useEffect(() => {
    if (!isProcessing) return;
    const interval = window.setInterval(async () => {
      try {
        const p = await api.getProgress();
        setProgress(p);
        if (p.daXong) {
          setIsProcessing(false);
          setResults(p.ketQua || []);
        }
      } catch { /* ignore */ }
    }, 400);
    return () => clearInterval(interval);
  }, [isProcessing]);

  const handleStart = useCallback(async () => {
    if (!folder) return;
    setResults([]);
    setProgress(null);
    const nen = settings.nen === '__mau__' ? settings.mauTuChon : settings.nen;
    const res = await api.startProcessing({
      thuMuc: folder,
      sau: recursive,
      nen,
      nhanh: settings.chatLuong === -1,
      maxsize: settings.chatLuong > 0 ? settings.chatLuong : 0,
      mask: settings.mask,
      thuMucRa: settings.thuMucRa,
      model: settings.model,
    });
    if (res.ok) {
      setIsProcessing(true);
    }
  }, [folder, recursive, settings]);

  const handleStop = useCallback(async () => {
    await api.stopProcessing();
  }, []);

  const outputDir = progress?.thuMucRa || settings.thuMucRa || '';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Header */}
        <header className="border-b border-slate-800 pb-5">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Tách Nền Pro
          </h1>
          <p className="text-slate-400 mt-1">
            Xóa nền ảnh hàng loạt bằng AI — chạy hoàn toàn trên máy, ảnh không gửi đi đâu.
          </p>
        </header>

        {/* Main layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left panel */}
          <div className="lg:col-span-5 space-y-5">
            <FolderSelector
              folder={folder}
              imageCount={imageCount}
              recursive={recursive}
              onFolderChange={setFolder}
              onRecursiveChange={setRecursive}
              onImageCountChange={setImageCount}
            />
            <Settings settings={settings} onChange={setSettings} />
          </div>

          {/* Right panel */}
          <div className="lg:col-span-7 space-y-5">
            <ProcessingPanel
              isProcessing={isProcessing}
              progress={progress}
              folderSelected={!!folder && imageCount > 0}
              onStart={handleStart}
              onStop={handleStop}
              onOpenFolder={() => outputDir && api.openFolder(outputDir)}
            />
            {results.length > 0 && !isProcessing && (
              <ResultsGallery results={results} visible />
            )}
          </div>
        </div>

        {/* Compare section */}
        <CompareView nen={settings.nen === '__mau__' ? settings.mauTuChon : settings.nen} />
      </div>
    </div>
  );
}
