import type { DirListing, Progress, ProcessingOptions } from './types';

// The server replaces __MA__ in index.html, or we can look for meta tag
declare global {
  interface Window {
    __MA__?: string;
  }
}

// Fallback to empty string for dev, should be replaced in prod
const MA_TOKEN = window.__MA__ && !window.__MA__.includes('%')
  ? window.__MA__ 
  : document.querySelector('meta[name="ma-token"]')?.getAttribute('content') || 'dev';

const headers = {
  'Content-Type': 'application/json',
  'X-Ma': MA_TOKEN
};

export const api = {
  async listDir(path: string): Promise<DirListing> {
    const params = new URLSearchParams({ duong: path, ma: MA_TOKEN });
    const res = await fetch(`/api/thu-muc?${params.toString()}`, { headers });
    if (!res.ok) throw new Error('Failed to list directory');
    return res.json();
  },

  async countImages(path: string, recursive: boolean): Promise<number> {
    const params = new URLSearchParams({ duong: path, sau: recursive ? '1' : '0', ma: MA_TOKEN });
    const res = await fetch(`/api/dem?${params.toString()}`, { headers });
    if (!res.ok) throw new Error('Failed to count images');
    const data = await res.json();
    return data.so;
  },

  async getProgress(): Promise<Progress> {
    const params = new URLSearchParams({ ma: MA_TOKEN });
    const res = await fetch(`/api/tien-trinh?${params.toString()}`, { headers });
    if (!res.ok) throw new Error('Failed to get progress');
    return res.json();
  },

  async listModels(): Promise<{id: string, ten: string, moTa: string, coSan: boolean}[]> {
    const params = new URLSearchParams({ ma: MA_TOKEN });
    const res = await fetch(`/api/models?${params.toString()}`, { headers });
    if (!res.ok) return [];
    const data = await res.json();
    return data.models || [];
  },

  async startProcessing(options: ProcessingOptions): Promise<{ok: boolean, tong?: number, loi?: string}> {
    const res = await fetch('/api/bat-dau', {
      method: 'POST',
      headers,
      body: JSON.stringify(options)
    });
    return res.json();
  },

  async stopProcessing(): Promise<void> {
    await fetch('/api/dung', {
      method: 'POST',
      headers
    });
  },

  async openFolderDialog(title: string, startDir: string, recursive: boolean): Promise<{duong?: string, so?: number, cancelled?: boolean, fallback?: boolean}> {
    const res = await fetch('/api/hop-thoai', {
      method: 'POST',
      headers,
      body: JSON.stringify({ tieuDe: title, batDau: startDir, sau: recursive })
    });
    
    const data = await res.json();
    if (data.huy) return { cancelled: true };
    if (data.khongCo) return { fallback: true };
    return data;
  },

  async openFolder(path: string): Promise<void> {
    await fetch('/api/mo', {
      method: 'POST',
      headers,
      body: JSON.stringify({ duong: path })
    });
  },

  getImageUrl(path: string, height: number): string {
    const params = new URLSearchParams({ duong: path, cao: height.toString(), ma: MA_TOKEN });
    return `/api/anh?${params.toString()}`;
  },

  getDownloadUrl(path: string): string {
    const params = new URLSearchParams({ duong: path, ma: MA_TOKEN });
    return `/api/tai?${params.toString()}`;
  },

  async uploadFiles(formData: FormData): Promise<{thuMuc: string, so: number}> {
    const res = await fetch('/api/upload?ma=' + MA_TOKEN, {
      method: 'POST',
      headers: { 'X-Ma': MA_TOKEN },
      body: formData,
    });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  },

  async compareModels(imagePath: string, nen: string): Promise<{ketQua: {model: string, ten: string, duong?: string, giay?: number, phu?: number, loi?: string}[]}> {
    const res = await fetch('/api/so-sanh', {
      method: 'POST',
      headers,
      body: JSON.stringify({ duong: imagePath, nen }),
    });
    if (!res.ok) throw new Error('Compare failed');
    return res.json();
  }
};
