export interface DirListing {
  duong: string;
  cha: string;
  thuMuc: string[];
  soAnh: number;
  laGoc: boolean;
}

export interface Progress {
  dangChay: boolean;
  daXong: boolean;
  tong: number;
  xong: number;
  loi: number;
  hienTai: string;
  nhatKy: string[];
  ketQua: string[];
  thuMucRa: string;
  giay: number;
  con: number;
}

// Alias used by UI components
export type ProgressData = Progress;

export interface ProcessingOptions {
  thuMuc: string;
  sau: boolean;
  nen: string;
  nhanh: boolean;
  maxsize: number;
  mask: boolean;
  thuMucRa: string;
  model: string;
}

export interface AppSettings {
  nen: string;
  chatLuong: number;
  thuMucRa: string;
  mask: boolean;
  mauTuChon: string;
  model: string;
}
