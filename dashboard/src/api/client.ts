const BASE = "/api";

export async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  overview: () => fetchAPI<any>("/overview"),
  transaksi: () => fetchAPI<{ data: any[]; total: number }>("/transaksi"),
  anggaran: () => fetchAPI<any>("/anggaran"),
  goals: () => fetchAPI<{ data: any[] }>("/goals"),
  investasi: () => fetchAPI<any>("/investasi"),
  kalkRumah: () => fetchAPI<any>("/kalkulator/rumah"),
  kalkKredit: () => fetchAPI<any>("/kalkulator/kredit"),
  kalkPensiun: () => fetchAPI<any>("/kalkulator/pensiun"),
  kalkTabunganPensiun: () => fetchAPI<any>("/kalkulator/tabungan-pensiun"),
  kalkUtang: () => fetchAPI<any>("/kalkulator/utang"),
};
