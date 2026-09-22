import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Cpu } from 'lucide-react';
import type { AppSettings } from '../types';
import { api } from '../api';

interface ModelInfo { id: string; ten: string; moTa: string; coSan: boolean; }

interface Props {
  settings: AppSettings;
  onChange: (s: AppSettings) => void;
}

export default function Settings({ settings, onChange }: Props) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  
  useEffect(() => {
    api.listModels().then(setModels).catch(() => {});
  }, []);

  const set = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    onChange({ ...settings, [key]: value });
  };

  return (
    <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-700/60">
      <h2 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-100">
        <SettingsIcon size={18} className="text-blue-400" />
        Tùy chọn
      </h2>

      <div className="space-y-4">
        {/* Model selector */}
        {models.length > 1 && (
          <div>
            <label className="block text-sm text-slate-400 mb-1.5 flex items-center gap-1.5">
              <Cpu size={14} /> Model tách nền
            </label>
            <div className="space-y-1.5">
              {models.filter(m => m.coSan).map(m => (
                <label
                  key={m.id}
                  className={`flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-all
                    ${settings.model === m.id 
                      ? 'border-blue-500 bg-blue-500/10' 
                      : 'border-slate-700 bg-slate-950 hover:border-slate-600'
                    }`}
                >
                  <input
                    type="radio"
                    name="model"
                    value={m.id}
                    checked={settings.model === m.id}
                    onChange={() => set('model', m.id)}
                    className="accent-blue-500"
                  />
                  <div>
                    <div className="text-sm text-slate-200 font-medium">{m.ten}</div>
                    <div className="text-xs text-slate-500">{m.moTa}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Background */}
        <div>
          <label className="block text-sm text-slate-400 mb-1.5">Nền thay thế</label>
          <div className="flex gap-2">
            <select
              value={settings.nen}
              onChange={(e) => set('nen', e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="trong">Trong suốt (PNG)</option>
              <option value="trang">Trắng</option>
              <option value="den">Đen</option>
              <option value="xanh">Xanh ảnh thẻ</option>
              <option value="do">Đỏ</option>
              <option value="xam">Xám</option>
              <option value="__mau__">Màu tự chọn…</option>
            </select>
            {settings.nen === '__mau__' && (
              <input
                type="color"
                value={settings.mauTuChon}
                onChange={(e) => set('mauTuChon', e.target.value)}
                className="w-10 h-10 p-0 border border-slate-700 rounded-lg bg-slate-950 cursor-pointer"
              />
            )}
          </div>
        </div>

        {/* Quality */}
        <div>
          <label className="block text-sm text-slate-400 mb-1.5">Chất lượng</label>
          <select
            value={settings.chatLuong}
            onChange={(e) => set('chatLuong', parseInt(e.target.value))}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value={0}>Tinh biên — đẹp nhất, chậm nhất</option>
            <option value={3000}>Tinh biên, hạ cỡ 3000</option>
            <option value={2500}>Tinh biên, hạ cỡ 2500 — khuyên dùng</option>
            <option value={1800}>Tinh biên, hạ cỡ 1800 — nhanh</option>
            <option value={-1}>Thô — nhanh nhất, biên tóc xấu</option>
          </select>
        </div>

        {/* Output folder */}
        <div>
          <label className="block text-sm text-slate-400 mb-1.5">Lưu kết quả vào</label>
          <input
            type="text"
            value={settings.thuMucRa}
            onChange={(e) => set('thuMucRa', e.target.value)}
            placeholder='Mặc định: thư mục "tachnen" cạnh ảnh gốc'
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Save mask */}
        <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-300 pt-1">
          <input
            type="checkbox"
            checked={settings.mask}
            onChange={(e) => set('mask', e.target.checked)}
            className="rounded accent-blue-500"
          />
          Lưu kèm mặt nạ alpha
        </label>
      </div>
    </div>
  );
}
