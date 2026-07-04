export interface Transaksi {
  tanggal: string;
  tanggal_raw: string;
  tipe: "Pemasukan" | "Pengeluaran" | "Transfer";
  jumlah: number;
  jumlah_fmt: string;
  kategori: string;
  keterangan: string;
}

export interface BudgetItem {
  kategori: string;
  anggaran: number;
  total_aktual: number;
  bulanan: { bulan: string; nilai: number }[];
}

export interface Goal {
  nama: string;
  target: number;
  terkumpul: number;
  persen: number;
  status: string;
}

export interface InvestasiAccount {
  nama: string;
  invested: number;
  value: number;
  gain_loss: number;
  persen: number;
}

export interface Overview {
  total_pemasukan: number;
  total_pengeluaran: number;
  saldo_bersih: number;
  total_investasi: number;
  spending_by_kategori: { kategori: string; jumlah: number }[];
}

export interface KalkulatorUtangItem {
  kreditur: string;
  sisa_hutang: number;
  bunga_tahunan: string;
  min_pembayaran: number;
}
