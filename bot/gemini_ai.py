import os
import json
import logging
import re
import time
from google import genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors

from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, NON_BUDGET_CATEGORIES,
    DAFTAR_AKUN, AKUN_KEYWORDS, FALLBACK_KEYWORDS, KATEGORI_EMOJI
)

logger = logging.getLogger(__name__)

TEXT_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

VISION_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]

_EXPENSE_LIST = '", "'.join(EXPENSE_CATEGORIES)
_INCOME_LIST  = '", "'.join(INCOME_CATEGORIES)
_ALL_CATS     = '", "'.join(EXPENSE_CATEGORIES + INCOME_CATEGORIES + NON_BUDGET_CATEGORIES)


class QuotaExhaustedError(Exception):
    pass


class GeminiAI:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        self.client = genai.Client(api_key=api_key)
        logger.info("Gemini AI initialized.")

    def _call(self, model: str, contents) -> str:
        return self.client.models.generate_content(model=model, contents=contents).text

    def _generate(self, prompt: str) -> str:
        last_error = None
        for model in TEXT_MODELS:
            try:
                result = self._call(model, prompt)
                logger.info(f"Text model used: {model}")
                return result
            except genai_errors.ClientError as e:
                err = str(e)
                if "429" in err:
                    delay = _parse_retry_delay(err)
                    logger.warning(f"Quota {model}, delay={delay}s")
                    if delay and delay <= 10:
                        time.sleep(delay + 1)
                        try:
                            return self._call(model, prompt)
                        except Exception:
                            pass
                    last_error = e
                    continue
                elif "404" in err:
                    last_error = e
                    continue
                raise
            except Exception as e:
                logger.error(f"Gemini error {model}: {e}")
                raise
        raise QuotaExhaustedError("Semua model Gemini mencapai batas kuota.")

    def _generate_vision(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        parts = [
            genai_types.Part(
                inline_data=genai_types.Blob(mime_type=mime_type, data=image_bytes)
            ),
            genai_types.Part(text=prompt),
        ]
        last_error = None
        for model in VISION_MODELS:
            try:
                result = self._call(model, parts)
                logger.info(f"Vision model used: {model}")
                return result
            except genai_errors.ClientError as e:
                err = str(e)
                if "429" in err:
                    delay = _parse_retry_delay(err)
                    logger.warning(f"Quota {model}, delay={delay}s")
                    if delay and delay <= 60:
                        time.sleep(delay + 1)
                        try:
                            return self._call(model, parts)
                        except Exception:
                            pass
                    last_error = e
                    continue
                elif "404" in err:
                    last_error = e
                    continue
                raise
            except Exception as e:
                logger.error(f"Vision error {model}: {e}")
                raise
        raise QuotaExhaustedError("Semua model vision Gemini mencapai batas kuota.")

    def _strip_json(self, raw: str) -> str:
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
        return raw

    def parse_transaction(self, text: str) -> dict | None:
        prompt = (
            "Kamu adalah Oliv, asisten keuangan pribadi milik Zee.\n"
            "Analisis teks transaksi dan kembalikan JSON.\n\n"
            "Format JSON:\n"
            "{\n"
            '  "tipe": "Pengeluaran" atau "Pemasukan",\n'
            '  "jumlah": angka bulat (contoh: "10.000"→10000, "2 juta"→2000000, "50k"→50000),\n'
            f'  "kategori": pilih dari: "{_ALL_CATS}",\n'
            '  "memo": nama barang/item yang dibeli (maks 3 kata, contoh: "Kopi", "Nasi Padang", "Bensin"),\n'
            '  "payee": keterangan lengkap transaksi (toko + konteks + alasan, bebas panjang),\n'
            '  "akun": nama akun (Cash, BCA, GoPay, ShopeePay, DANA, RDN, Jago, Tabungan 27Th, Dana Darurat, Investasi),\n'
            "}\n\n"
            "Panduan kategori:\n"
            "- Makan/minum/kopi/rokok → Makan & Minum\n"
            "- Grab/Gojek/bensin/parkir/tol → Transportasi\n"
            "- Pulsa/kuota/wifi/internet → Pulsa / Internet\n"
            "- Listrik/air/gas/cicilan/asuransi → Cicilan & Tagihan\n"
            "- Bioskop/game/Netflix/Spotify/gym → Hiburan & Lifestyle\n"
            "- Sewa/kos/renovasi → Tempat Tinggal (Housing)\n"
            "- Dokter/obat/apotek → Kesehatan\n"
            "- Baju/sepatu/tas/skincare/elektronik → Belanja Pakaian & Barang\n"
            "- Kursus/buku/sekolah → Pendidikan\n"
            "- Sedekah/infaq/donasi/hadiah → Hadiah & Sosial\n"
            "- Supplies/marketing/iklan → Bisnis\n"
            "- Gaji → Gaji\n"
            "- Bonus/THR → Bonus\n"
            "- Dividen/saham → Dividen\n"
            "- Freelance/jualan → Usaha\n\n"
            "Panduan memo vs payee:\n"
            "- memo: NAMA BARANG/ITEM SINGKAT (1-3 kata). Contoh: 'Kopi', 'Nasi Goreng', 'Bensin', 'Oli Motor'\n"
            "- payee: KETERANGAN LENGKAP. Contoh: 'Kopi Kenangan - meeting client, jalan Thamrin', 'SPBU Pertamina 34.123.07 - isi bensin motor'\n"
            "- Kalau user bilang 'beli kopi 15rb di kopi kenangan buat meeting' → memo='Kopi', payee='Kopi Kenangan - beli kopi 15rb buat meeting'\n\n"
            "PENTING:\n"
            "- Rokok SELALU 'Makan & Minum'\n"
            "- Transfer antar akun → kategori '[Transfer]'\n"
            "- Kembalikan HANYA JSON, tanpa penjelasan, tanpa ```\n\n"
            f'Teks: "{text}"'
        )
        try:
            raw = self._strip_json(self._generate(prompt))
            data = json.loads(raw)
            if data.get("tipe") is None:
                return None

            akun = data.get("akun", "Cash")
            if akun not in DAFTAR_AKUN:
                akun = "Cash"

            return {
                "tipe":       str(data["tipe"]),
                "jumlah":     float(data["jumlah"]),
                "kategori":   str(data["kategori"]),
                "memo":       str(data.get("memo", "-")),
                "payee":      str(data.get("payee", "-")),
                "akun":       akun,
            }
        except QuotaExhaustedError:
            raise
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"JSON parse failed: {e} | raw: {raw!r}")
            return None

    def parse_receipt_photo(self, image_bytes: bytes, mime_type: str) -> dict | None:
        prompt = (
            "Kamu adalah Oliv, asisten keuangan pribadi milik Zee.\n"
            "Analisis foto struk/nota/receipt ini.\n\n"
            "Ekstrak informasi dan kembalikan HANYA JSON:\n"
            "{\n"
            '  "tipe": "Pengeluaran",\n'
            '  "jumlah": total yang dibayar (angka bulat, tanpa simbol),\n'
            f'  "kategori": pilih dari: "{_EXPENSE_LIST}",\n'
            '  "memo": nama barang/item utama (maks 3 kata, contoh: "Kopi", "Nasi", "Bensin"),\n'
            '  "payee": nama toko + keterangan lengkap (bebas panjang),\n'
            '  "items": item utama yang dibeli, pisahkan koma (maks 5 item),\n'
            '  "akun": deteksi akun dari struk (Cash, GoPay, BCA, dll)\n'
            "}\n\n"
            "Panduan kategori:\n"
            "- Indomaret/Alfamart/minimarket → lihat isi: makanan/minum → Makan & Minum, produk rumah → Belanja Pakaian & Barang\n"
            "- Restoran/warung/kafe → Makan & Minum\n"
            "- Apotek/klinik/RS → Kesehatan\n"
            "- Grab/Gojek/bensin/parkir/tol → Transportasi\n"
            "- Supermarket/dept store → Belanja Pakaian & Barang\n"
            "- Listrik/air/internet/pulsa → Cicilan & Tagihan\n"
            "- Bioskop/game/rekreasi → Hiburan & Lifestyle\n"
            "- Salon/spa/barbershop → Perawatan Diri\n"
            "- Toko HP/elektronik → Gadget & Elektronik\n\n"
            "Panduan memo vs payee:\n"
            "- memo: NAMA BARANG SINGKAT. Contoh: 'Kopi', 'Mie Instan', 'Shampoo'\n"
            "- payee: NAMA TOKO + KONTEKS. Contoh: 'Indomaret Jl. Sudirman - beli kopi & mie', 'Starbucks Mall Taman Anggrek - meeting client'\n\n"
            "Jika BUKAN struk belanja: {\"tipe\": null}\n\n"
            "PENTING: Kembalikan HANYA JSON, tanpa penjelasan, tanpa ```."
        )
        try:
            raw = self._strip_json(self._generate_vision(image_bytes, mime_type, prompt))
            data = json.loads(raw)
            if data.get("tipe") is None:
                return None

            akun = data.get("akun", "Cash")
            if akun not in DAFTAR_AKUN:
                akun = "Cash"

            return {
                "tipe":       str(data["tipe"]),
                "jumlah":     float(data["jumlah"]),
                "kategori":   str(data["kategori"]),
                "memo":       str(data.get("memo", "-")),
                "payee":      str(data.get("payee", "-")),
                "items":      str(data.get("items", "")),
                "akun":       akun,
            }
        except QuotaExhaustedError:
            raise
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Receipt JSON parse failed: {e} | raw: {raw!r}")
            return None

    def generate_weekly_report(self, transactions: list[dict], name: str) -> str:
        if not transactions:
            return (
                f"Hei {name}! Minggu ini belum ada transaksi yang tercatat nih 😅 "
                "Mulai catat ya supaya aku bisa bantu analisis keuanganmu!"
            )
        rows = "\n".join(
            f"{t.get('tgl','')} | {t.get('kategori','')} | Rp{float(t.get('payment',0)):,.0f} | {t.get('memo','')}"
            for t in transactions if t.get('payment', 0) > 0
        )
        prompt = (
            f"Kamu adalah Oliv, asisten keuangan personal yang gaul dan supportif. "
            f"Buat laporan keuangan mingguan untuk {name}.\n\n"
            f"Data transaksi (Tanggal | Kategori | Jumlah | Memo):\n{rows}\n\n"
            f"Laporan harus:\n"
            f"1. Sapa {name} dengan hangat\n"
            f"2. Total pengeluaran minggu ini\n"
            f"3. Kategori pengeluaran terbesar\n"
            f"4. 1-2 saran/insight actionable\n"
            f"5. Motivasi penutup\n\n"
            f"Gunakan bahasa Indonesia casual, emoji secukupnya, format Markdown (bold angka penting). Maks 280 kata."
        )
        return self._generate(prompt)

    def ask(self, question: str, transactions: list[dict]) -> str:
        if transactions:
            rows = "\n".join(
                f"{t.get('tgl','')} | {t.get('kategori','')} | Rp{float(t.get('payment',0)):,.0f} | {t.get('memo','')}"
                for t in transactions
            )
            ctx = (
                "Kamu adalah Oliv, asisten keuangan pribadi Zee. "
                "Data transaksi Zee (Tanggal | Kategori | Jumlah | Memo):\n"
                f"{rows}\n\nPertanyaan: {question}\n\n"
                "Jawab singkat, jelas, gunakan angka spesifik. Bahasa Indonesia casual, gaya teman dekat."
            )
        else:
            ctx = (
                "Kamu adalah Oliv, asisten keuangan pribadi Zee. Belum ada transaksi.\n\n"
                f"Pertanyaan: {question}\n\nBerikan saran umum. Bahasa Indonesia casual, gaya teman dekat."
            )
        return self._generate(ctx)


def _parse_retry_delay(error_str: str) -> float | None:
    m = re.search(r"retry[_ ](?:in|delay)['\"]?\s*[:\s]+['\"]?(\d+(?:\.\d+)?)", error_str, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)s", error_str)
    return float(m.group(1)) if m else None
    