import os
import json
import logging
import re
from datetime import time as dt_time, timedelta

from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters,
)

from sheets import (
    tulis_transaksi, tulis_transfer, get_semua_transaksi,
    filter_operasional, saldo_per_akun, get_summary,
    get_recent, get_week_transactions,
    get_month_expense_for_category, get_anggaran_for_category,
    now_wib,
)
from sheets_manager import get_manager, list_spreadsheets, list_sheets
from gemini_ai import GeminiAI, QuotaExhaustedError
from config import (
    BOT_NAME, TIPE_PEMASUKAN, TIPE_PENGELUARAN,
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, ALL_CATEGORIES,
    DAFTAR_AKUN, AKUN_KEYWORDS, KATEGORI_EMOJI, KOMENTAR_OLIV,
    NON_BUDGET_CATEGORIES,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "")
if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN environment variable is not set.")
REGISTRY_FILE   = os.path.join(os.path.dirname(__file__), "user_registry.json")

ai     = GeminiAI()


def _load_reg():
    try:
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_reg(reg):
    try:
        with open(REGISTRY_FILE, "w") as f:
            json.dump(reg, f)
    except Exception as e:
        logger.error(f"Registry save failed: {e}")


_registry = _load_reg()


def _register(user, chat_id):
    key = str(chat_id)
    if key not in _registry:
        _registry[key] = {
            "first_name": user.first_name or "Kak",
            "full_name":  user.full_name or "",
        }
        _save_reg(_registry)


def rp(amount):
    return "Rp " + f"{amount:,.0f}".replace(",", ".")


def fname(user):
    return user.first_name or "Kak"


def emoji_kategori(kat):
    return KATEGORI_EMOJI.get(kat, "📌")


def komentar_personal(memo):
    import random
    ml = memo.lower()
    for kw, komentar_list in KOMENTAR_OLIV.items():
        if kw in ml:
            return random.choice(komentar_list)
    return None


def deteksi_akun(text):
    tl = text.lower()
    for akun, keywords in AKUN_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            return akun
    return "Cash"


def parse_transfer_accounts(text):
    """Parse 'dari X ke Y' atau deteksi 2 akun dari text"""
    text_lower = text.lower()

    # Pattern 1: "dari [akun] ke [akun]"
    match = re.search(r'dari\s+(\w+(?:\s+\w+)?)\s+ke\s+(\w+(?:\s+\w+)?)', text_lower)
    if match:
        dari_raw = match.group(1).strip()
        ke_raw = match.group(2).strip()

        dari = _map_to_akun(dari_raw)
        ke = _map_to_akun(ke_raw)
        if dari and ke:
            return dari, ke

    # Pattern 2: "ke [akun] dari [akun]"
    match = re.search(r'ke\s+(\w+(?:\s+\w+)?)\s+dari\s+(\w+(?:\s+\w+)?)', text_lower)
    if match:
        ke = _map_to_akun(match.group(1).strip())
        dari = _map_to_akun(match.group(2).strip())
        if dari and ke:
            return dari, ke

    # Fallback: cari 2 akun yang disebut
    found = []
    for akun in DAFTAR_AKUN:
        if akun.lower() in text_lower:
            found.append(akun)

    if len(found) >= 2:
        return found[0], found[1]
    elif len(found) == 1:
        return "Cash", found[0]

    return "Cash", "GoPay"


def _map_to_akun(raw_name):
    """Map nama bebas ke akun valid"""
    raw_lower = raw_name.lower()
    for akun in DAFTAR_AKUN:
        if akun.lower() == raw_lower:
            return akun
    for akun, keywords in AKUN_KEYWORDS.items():
        if any(kw in raw_lower for kw in keywords):
            return akun
    return None


async def _budget_alert(update, kategori):
    if kategori not in EXPENSE_CATEGORIES:
        return
    try:
        budget = get_anggaran_for_category(kategori)
        if budget <= 0:
            return
        spent = get_month_expense_for_category(kategori)
        ratio = spent / budget
        if ratio >= 1.0:
            await update.message.reply_text(
                f"🔴 *Budget Alert — {kategori} OVER!*\n\n"
                f"Pengeluaran *{kategori}* bulan ini udah *melebihi anggaran*!\n"
                f"Terpakai: `{rp(spent)}` / Anggaran: `{rp(budget)}` ({ratio*100:.0f}%)\n\n"
                f"Kurangi pengeluaran di kategori ini ya 💪",
                parse_mode="Markdown",
            )
        elif ratio >= 0.85:
            await update.message.reply_text(
                f"🟡 *Budget Warning — {kategori} Rawan!*\n\n"
                f"Pengeluaran *{kategori}* udah {ratio*100:.0f}% dari anggaran.\n"
                f"Terpakai: `{rp(spent)}` / Anggaran: `{rp(budget)}`\n\n"
                f"Hati-hati, jangan sampai over budget 🙏",
                parse_mode="Markdown",
            )
    except Exception as e:
        logger.error(f"Budget alert error: {e}")

async def start(update, context):
    user = update.effective_user
    name = fname(user)
    _register(user, update.effective_chat.id)
    await update.message.reply_text(
        f"Halo *{name}!* 👋 Aku *{BOT_NAME}*, asisten keuangan pribadimu~ 💸\n\n"
        f"Gak perlu ribet — langsung cerita atau kirim foto struk:\n\n"
        f"💬 _\"beli kopi 15rb di kopi kenangan\"_\n"
        f"💬 _\"gajian 5 juta\"_\n"
        f"💬 _\"bayar listrik 250rb\"_\n"
        f"📸 _Kirim foto struk → aku scan & catat otomatis!_\n\n"
        f"Semua langsung masuk Google Sheet kamu! 📊\n\n"
        f"*Perintah tersedia:*\n"
        f"📉 /pengeluaran — catat pengeluaran manual\n"
        f"📈 /pemasukan — catat pemasukan manual\n"
        f"📊 /ringkasan — ringkasan keuangan keseluruhan\n"
        f"💰 /saldo — cek saldo semua akun\n"
        f"📅 /hariini — pengeluaran hari ini\n"
        f"📈 /mingguini — 7 hari terakhir\n"
        f"🏆 /terbesar — top 10 pengeluaran\n"
        f"🔍 /analisa — Oliv baca pola keuanganmu\n"
        f"💰 /budget — cek status budget bulan ini\n"
        f"📋 /terakhir — 10 transaksi terakhir\n"
        f"🤖 /tanya — tanya Oliv soal keuanganmu\n"
        f"❓ /help — bantuan\n\n"
        f"Yuk mulai catat keuanganmu, {name}! 💪",
        parse_mode="Markdown",
    )


async def help_cmd(update, context):
    _register(update.effective_user, update.effective_chat.id)
    await start(update, context)


async def handle_free_text(update, context):
    user = update.effective_user
    name = fname(user)
    _register(user, update.effective_chat.id)
    text = update.message.text.strip()

    BUKAN_TRANSAKSI = [
        "haha", "hehe", "hihi", "wkwk", "lol", "oke", "ok",
        "iya", "yep", "yup", "makasih", "thanks", "mantap", "keren",
        "siap", "noted", "sip", "done", "selesai", "beres",
    ]
    tl = text.lower().strip()
    if tl in BUKAN_TRANSAKSI or (len(tl) <= 4 and not any(c.isdigit() for c in tl)):
        return

    await update.message.reply_text(f"Bentar ya {name}, aku proses dulu... ⏳")

    try:
        parsed = ai.parse_transaction(text)
    except QuotaExhaustedError:
        await update.message.reply_text(
            f"Waduh {name}, kuota Gemini habis nih 😓\n"
            f"Coba lagi besok ya!"
        )
        return
    except Exception as e:
        logger.error(f"AI error: {e}")
        await update.message.reply_text(f"Aduh {name}, AI-nya gangguan nih. Coba lagi ya! 🙏")
        return

    if parsed is None:
        await update.message.reply_text(
            f"Hmm, aku kurang nangkep maksudnya {name} 🤔\n\n"
            f"Coba tulis lebih jelas:\n"
            f"• _\"beli makan siang 25.000\"_\n"
            f"• _\"gajian 4 juta\"_\n"
            f"• _\"bayar grab 18rb\"_\n\n"
            f"Kalau mau tanya, pakai /tanya ya!",
            parse_mode="Markdown",
        )
        return

    if parsed["kategori"] == "[Transfer]":
        dari_akun, ke_akun = parse_transfer_accounts(text)
        if dari_akun == ke_akun:
            ke_akun = "GoPay"
        try:
            tulis_transfer(dari_akun, ke_akun, int(parsed["jumlah"]), parsed.get("payee", "Pindah Saldo"))
            await update.message.reply_text(
                f"🔁 *Transfer Tercatat!*\n"
                f"*{dari_akun}* → *{ke_akun}*\n"
                f"💰 {rp(parsed['jumlah'])}\n✅ Cleared",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            await update.message.reply_text(f"Duh {name}, gagal nyimpen nih. Coba lagi! 😓")
        return

    try:
        if parsed["tipe"] == TIPE_PENGELUARAN:
            tulis_transaksi(
                akun=parsed.get("akun", "Cash"),
                payee=parsed.get("payee", "-"),
                memo=parsed["memo"],
                kategori=parsed["kategori"],
                payment=int(parsed["jumlah"]),
                deposit="",
            )
            em = emoji_kategori(parsed["kategori"])
            komentar = komentar_personal(parsed["memo"])
            msg = (
                f"✅ *Tercatat, {name}!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{em} *{parsed['memo'].title()}* — {rp(parsed['jumlah'])}\n"
                f"📂 {parsed['kategori']}  |  🏪 {parsed.get('payee', '-')}  |  💳 {parsed.get('akun', 'Cash')}"
            )
            if komentar:
                msg += f"\n_{komentar}_"
            await update.message.reply_text(msg, parse_mode="Markdown")
            await _budget_alert(update, parsed["kategori"])
        else:
            tulis_transaksi(
                akun=parsed.get("akun", "Cash"),
                payee=parsed.get("payee", "-"),
                memo=parsed["memo"],
                kategori=parsed["kategori"],
                payment="",
                deposit=int(parsed["jumlah"]),
            )
            await update.message.reply_text(
                f"💼 *Pemasukan Tercatat!*\n"
                f"💰 {rp(parsed['jumlah'])} ke *{parsed.get('akun', 'Cash')}*\n"
                f"📦 Kategori: {parsed['kategori']}\n"
                f"📝 Memo: {parsed['memo']}\n✅ Cleared",
                parse_mode="Markdown",
            )
    except Exception as e:
        logger.error(f"Sheets error: {e}")
        await update.message.reply_text(f"Duh {name}, gagal nyimpen ke Sheet nih 😓 Coba lagi!")


async def handle_photo(update, context):
    user = update.effective_user
    name = fname(user)
    _register(user, update.effective_chat.id)

    await update.message.reply_text(f"Ada struk nih {name}! Bentar, aku scan... 📸🔍")

    try:
        photo     = update.message.photo[-1]
        tg_file   = await context.bot.get_file(photo.file_id)
        img_bytes = bytes(await tg_file.download_as_bytearray())
        parsed    = ai.parse_receipt_photo(img_bytes, "image/jpeg")
    except QuotaExhaustedError:
        await update.message.reply_text(f"Waduh {name}, kuota Gemini habis nih 😓 Coba lagi nanti ya!")
        return
    except Exception as e:
        logger.error(f"Receipt scan error: {e}")
        await update.message.reply_text(
            f"Aduh {name}, gagal scan struknya 😓\n"
            f"Pastiin foto cukup terang dan angka totalnya keliatan ya!"
        )
        return

    if parsed is None:
        await update.message.reply_text(
            f"Hmm, kayaknya ini bukan struk belanja deh {name} 🤔\n\n"
            f"Coba kirim foto struk yang lebih jelas ya!"
        )
        return

    try:
        tulis_transaksi(
            akun=parsed.get("akun", "Cash"),
            payee=parsed.get("payee", "-"),
            memo=parsed["memo"],
            kategori=parsed["kategori"],
            payment=int(parsed["jumlah"]),
            deposit="",
        )
    except Exception as e:
        logger.error(f"Sheets error (receipt): {e}")
        await update.message.reply_text(f"Duh {name}, gagal nyimpen ke Sheet nih 😓 Coba lagi!")
        return

    items_line = f"\n📦 _Item: {parsed['items']}_" if parsed.get("items") else ""
    em = emoji_kategori(parsed["kategori"])
    komentar = komentar_personal(parsed["memo"])

    msg = (
        f"✅ *Struk berhasil di-scan, {name}!*\n\n"
        f"{em} *{parsed['memo'].title()}*\n"
        f"💰 Total: `{rp(parsed['jumlah'])}`\n"
        f"🏪 Payee: {parsed.get('payee', '-')}\n"
        f"🏷️ Kategori: {parsed['kategori']}"
        f"{items_line}\n"
        f"💳 Akun: {parsed.get('akun', 'Cash')}"
    )
    if komentar:
        msg += f"\n_{komentar}_"

    await update.message.reply_text(msg, parse_mode="Markdown")
    await _budget_alert(update, parsed["kategori"])

async def pengeluaran(update, context):
    user = update.effective_user
    name = fname(user)
    _register(user, update.effective_chat.id)
    args = context.args

    if not args or len(args) < 2:
        cats = ", ".join(EXPENSE_CATEGORIES[:6]) + ", ..."
        await update.message.reply_text(
            f"Cara pakainya, {name}:\n"
            f"`/pengeluaran <jumlah> <kategori> [memo] [payee] [akun]`\n\n"
            f"Contoh: `/pengeluaran 45000 \"Makan & Minum\" Kopi \"Kopi Kenangan - meeting\" gopay`\n\n"
            f"Kategori: _{cats}_\n"
            f"Akun: Cash, BCA, GoPay, ShopeePay, DANA, RDN, Jago, Tabungan 27Th, Dana Darurat, Investasi\n\n"
            f"💡 _Atau langsung ketik: \"beli makan 45 ribu\"_\n"
            f"📸 _Atau kirim foto struk!_",
            parse_mode="Markdown",
        )
        return

    try:
        jumlah = float(str(args[0]).replace(".", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text(
            f"Jumlahnya harus angka ya {name} 😄\n"
            f"Contoh: `/pengeluaran 45000 \"Makan & Minum\" Kopi \"Kopi Kenangan\"`",
            parse_mode="Markdown",
        )
        return

    kategori = None
    memo = "-"
    payee = "-"
    akun = "Cash"

    if args[1] in EXPENSE_CATEGORIES or args[1] in INCOME_CATEGORIES:
        kategori = args[1]
        remaining = args[2:]
    else:
        for i in range(1, len(args)):
            cat_candidate = " ".join(args[1:i+1])
            if cat_candidate in EXPENSE_CATEGORIES or cat_candidate in INCOME_CATEGORIES:
                kategori = cat_candidate
                remaining = args[i+1:]
                break

    if not kategori:
        await update.message.reply_text(f"Kategori nggak ketemu ya {name} 😅 Coba yang ada di daftar!")
        return

    for arg in remaining:
        arg_lower = arg.lower()
        if arg in DAFTAR_AKUN or any(arg_lower == a.lower() for a in DAFTAR_AKUN):
            akun = arg
        elif len(arg) > 15 or " " in arg:
            payee = arg
        else:
            memo = arg

    if memo == "-" and remaining:
        memo = remaining[0]
    if payee == "-" and len(remaining) > 1:
        payee = " ".join(remaining[1:])

    try:
        tulis_transaksi(akun, payee, memo, kategori, int(jumlah), "")
        await update.message.reply_text(
            f"Siap, {name}! Pengeluaran *{rp(jumlah)}* buat *{memo}* "
            f"({kategori}) dari *{akun}* udah {BOT_NAME} catat. 📝✅\n"
            f"🏪 Payee: {payee}",
            parse_mode="Markdown",
        )
        await _budget_alert(update, kategori)
    except Exception as e:
        logger.error(f"Pengeluaran error: {e}")
        await update.message.reply_text(f"Aduh {name}, gagal nyimpen nih. Coba lagi ya! 😓")


async def pemasukan(update, context):
    user = update.effective_user
    name = fname(user)
    _register(user, update.effective_chat.id)
    args = context.args

    if not args or len(args) < 2:
        await update.message.reply_text(
            f"Cara pakainya, {name}:\n"
            f"`/pemasukan <jumlah> <kategori> [memo] [payee] [akun]`\n\n"
            f"Contoh: `/pemasukan 5000000 Gaji Gaji \"Gaji Juni 2026\" bca`\n\n"
            f"Kategori: Gaji, Bonus, Dividen, Usaha, Lain-lain\n"
            f"Akun: Cash, BCA, GoPay, ShopeePay, DANA, RDN, Jago, Tabungan 27Th, Dana Darurat, Investasi\n\n"
            f"💡 _Atau langsung ketik: \"gajian 5 juta\"_",
            parse_mode="Markdown",
        )
        return

    try:
        jumlah = float(str(args[0]).replace(".", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text(f"Jumlahnya harus angka ya {name} 😄")
        return

    kategori = args[1]
    memo = "-"
    payee = "-"
    akun = "Cash"

    for arg in args[2:]:
        if arg in DAFTAR_AKUN:
            akun = arg
        elif len(arg) > 15:
            payee = arg
        else:
            memo = arg

    try:
        tulis_transaksi(akun, payee, memo, kategori, "", int(jumlah))
        await update.message.reply_text(
            f"Yeay, ada pemasukan nih {name}! 🎉 *{rp(jumlah)}* dari *{memo}* "
            f"({kategori}) ke *{akun}* udah {BOT_NAME} catat. 📝✅\n"
            f"🏪 Payee: {payee}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Pemasukan error: {e}")
        await update.message.reply_text(f"Aduh {name}, gagal nyimpen nih. Coba lagi ya! 😓")


async def ringkasan(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    await update.message.reply_text(f"Bentar {name}, aku rekap dulu... 📊")

    try:
        data = get_summary()
        saldo = data["saldo"]
        emoji = "🟢" if saldo >= 0 else "🔴"
        note  = "Keuanganmu sehat nih!" if saldo >= 0 else "Hati-hati, pengeluaran > pemasukan ya!"

        cat_lines = ""
        if data["by_category"]:
            cat_lines = "\n\n*Pengeluaran per Kategori:*\n"
            for cat, amt in sorted(data["by_category"].items(), key=lambda x: -x[1])[:10]:
                em = emoji_kategori(cat)
                cat_lines += f"  {em} {cat}: `{rp(amt)}`\n"

        await update.message.reply_text(
            f"Ini rekap keuangan kamu, {name}! 💼\n\n"
            f"📈 Total Pemasukan: `{rp(data['total_income'])}`\n"
            f"📉 Total Pengeluaran: `{rp(data['total_expense'])}`\n"
            f"{emoji} Saldo: `{rp(saldo)}`\n"
            f"📋 Total Transaksi: `{data['transactions']}`\n\n"
            f"_{note}_"
            f"{cat_lines}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Ringkasan error: {e}")
        await update.message.reply_text(f"Aduh {name}, gagal ngambil data nih. Coba lagi ya! 😓")


async def saldo_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)

    try:
        semua = get_semua_transaksi()
        saldo = saldo_per_akun(semua)
        baris = ""
        total = 0
        for akun in DAFTAR_AKUN:
            if akun in saldo:
                s = saldo[akun]
                total += s
                baris += f"{akun:<15} {rp(s)}\n"
        for akun, s in saldo.items():
            if akun not in DAFTAR_AKUN:
                total += s
                baris += f"{akun:<15} {rp(s)}\n"

        await update.message.reply_text(
            f"💰 *Saldo Saat Ini*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"`{baris}`"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Total Aset:* {rp(total)}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Saldo error: {e}")
        await update.message.reply_text(f"Aduh {name}, gagal ngambil data nih. 😓")


async def hariini_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)

    hari_ini = now_wib().strftime("%Y-%m-%d")
    semua = get_semua_transaksi()
    data = [t for t in filter_operasional(semua) if t["tgl"] == hari_ini and t["payment"] > 0]

    if not data:
        await update.message.reply_text(f"📭 Belum ada pengeluaran hari ini, {name}.")
        return

    baris = ""
    total = 0
    for t in data:
        em = emoji_kategori(t["kategori"])
        label = t["memo"].title() if t["memo"] else t["kategori"]
        baris += f"{em} {label}\n{rp(t['payment'])}\n\n"
        total += t["payment"]

    await update.message.reply_text(
        f"📅 *Pengeluaran Hari Ini*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{baris}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💸 *Total:* {rp(total)}",
        parse_mode="Markdown",
    )


async def mingguini_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)

    semua = get_semua_transaksi()
    hari_ini = now_wib().date()
    tujuh_lalu = hari_ini - timedelta(days=6)
    data = []
    for t in filter_operasional(semua):
        try:
            tgl_t = datetime.strptime(t["tgl"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if tujuh_lalu <= tgl_t <= hari_ini and t["payment"] > 0:
            data.append(t)

    if not data:
        await update.message.reply_text(f"📭 Tidak ada pengeluaran 7 hari terakhir, {name}.")
        return

    per_kat = {}
    total = 0
    for t in data:
        per_kat[t["kategori"]] = per_kat.get(t["kategori"], 0) + t["payment"]
        total += t["payment"]

    baris = ""
    for kat, jml in sorted(per_kat.items(), key=lambda x: -x[1]):
        em = emoji_kategori(kat)
        persen = (jml / total * 100) if total else 0
        baris += f"{em} {kat}: {rp(jml)} ({persen:.0f}%)\n"

    await update.message.reply_text(
        f"📈 *Ringkasan 7 Hari Terakhir*\n"
        f"_{tujuh_lalu.strftime('%d %b')} – {hari_ini.strftime('%d %b %Y')}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{baris}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💸 *Total:* {rp(total)}\n"
        f"📝 {len(data)} transaksi",
        parse_mode="Markdown",
    )


async def terbesar_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)

    bulan_ini = now_wib().strftime("%Y-%m")
    semua = get_semua_transaksi()
    data = [t for t in filter_operasional(semua) if t["tgl"].startswith(bulan_ini) and t["payment"] > 0]

    if not data:
        await update.message.reply_text(f"📭 Belum ada transaksi bulan ini, {name}.")
        return

    top10 = sorted(data, key=lambda x: -x["payment"])[:10]
    nama_bulan = now_wib().strftime("%B %Y")
    baris = ""
    for i, t in enumerate(top10, 1):
        em = emoji_kategori(t["kategori"])
        label = t["memo"].title() if t["memo"] else t["kategori"]
        baris += f"{i}. {em} {label} — {rp(t['payment'])}\n"

    await update.message.reply_text(
        f"🏆 *Top 10 Pengeluaran Terbesar*\n"
        f"_{nama_bulan}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{baris}",
        parse_mode="Markdown",
    )


async def analisa_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)

    bulan_ini = now_wib().strftime("%Y-%m")
    nama_bulan = now_wib().strftime("%B %Y")
    semua = get_semua_transaksi()
    data = [t for t in filter_operasional(semua) if t["tgl"].startswith(bulan_ini) and t["payment"] > 0]

    if len(data) < 3:
        await update.message.reply_text(f"📭 Data transaksi masih sedikit, {name}. Coba lagi nanti ya!")
        return

    await update.message.reply_text(f"🔍 Bentar ya {name}, Oliv lagi baca transaksi kamu...")

    try:
        answer = ai.ask("analisa pola pengeluaran bulan ini", data)
        await update.message.reply_text(
            f"📊 *Analisa Oliv — {nama_bulan}*\n━━━━━━━━━━━━━━━━━━\n{answer}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Analisa error: {e}")
        await update.message.reply_text(f"Aduh {name}, gagal analisa nih. Coba lagi! 😓")


async def budget_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    await update.message.reply_text(f"Bentar {name}, aku cek budget bulan ini... 💰")

    try:
        lines = [f"💰 *Budget Status Bulan Ini*\n_(Anggaran vs Aktual)_\n"]
        has_budget = False
        any_warning = False

        for cat in EXPENSE_CATEGORIES:
            budget = get_anggaran_for_category(cat)
            if budget <= 0:
                continue
            has_budget = True
            spent = get_month_expense_for_category(cat)
            ratio = spent / budget

            if ratio >= 1.0:
                status = "🔴 OVER"
                any_warning = True
            elif ratio >= 0.85:
                status = "🟡 Rawan"
                any_warning = True
            else:
                status = "🟢 Aman"

            lines.append(
                f"*{cat}* — {status}\n"
                f"  `{rp(spent)}` / `{rp(budget)}` ({ratio*100:.0f}%)"
            )
        if not has_budget:
            await update.message.reply_text(
                f"Belum ada anggaran yang diatur nih, {name} 📭\n\n"
                f"Buka tab *Budget* di Google Sheet, isi kolom bulan ini "
                f"per kategori dulu ya! 🎯",
                parse_mode="Markdown",
            )
            return

        if not any_warning:
            lines.append("\n✨ _Semua kategori masih aman! Great job!_ 💪")

        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Budget cmd error: {e}")
        await update.message.reply_text(f"Aduh {name}, gagal cek budget nih. Coba lagi ya! 😓")

async def terakhir(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    await update.message.reply_text(f"Bentar {name}, aku ambil transaksi terakhir... 📋")

    try:
        txns = get_recent(10)
        if not txns:
            await update.message.reply_text(f"Belum ada transaksi nih {name}. Yuk mulai catat! 😊")
            return

        lines = []
        for t in txns:
            emoji = "📉" if t.get("payment", 0) > 0 else "📈"
            try:
                amt = float(t.get("payment", 0) or t.get("deposit", 0))
            except (ValueError, TypeError):
                amt = 0.0
            lines.append(
                f"{emoji} `{t.get('tgl','-')}` — *{t.get('kategori','-')}*\n"
                f"   `{rp(amt)}` — {t.get('memo','-')} ({t.get('akun','Cash')})"
            )

        await update.message.reply_text(
            f"10 transaksi terakhir kamu, {name}! 📋\n\n" + "\n\n".join(lines),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Terakhir error: {e}")
        await update.message.reply_text(f"Aduh {name}, gagal ngambil data nih. Coba lagi ya! 😓")


async def tanya(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)

    if not context.args:
        await update.message.reply_text(
            f"Tanya apa nih, {name}? 🤔\n\n"
            f"Cara pakainya: `/tanya <pertanyaanmu>`\n\n"
            f"Contoh: `/tanya berapa total makan bulan ini?`",
            parse_mode="Markdown",
        )
        return

    question = " ".join(context.args)
    await update.message.reply_text(f"Hmm, biar aku pikirin dulu {name}... 🤔💭")

    try:
        txns   = get_semua_transaksi()
        answer = ai.ask(question, txns)
        await update.message.reply_text(
            f"🤖 *Jawaban {BOT_NAME}:*\n\n{answer}", parse_mode="Markdown"
        )
    except QuotaExhaustedError:
        await update.message.reply_text(
            f"Waduh {name}, kuota Gemini habis nih 😓\n"
            f"Coba lagi besok ya!"
        )
    except Exception as e:
        logger.error(f"Tanya error: {e}")
        await update.message.reply_text(f"Aduh {name}, AI-nya lagi gangguan. Coba lagi sebentar! 🙏")


async def _send_weekly_report(context):
    reg = _load_reg()
    if not reg:
        logger.info("Weekly report: no registered users.")
        return

    logger.info(f"Sending weekly reports to {len(reg)} users...")
    txns = get_week_transactions()

    for chat_id_str, info in reg.items():
        try:
            name   = info.get("first_name", "Kak")
            report = ai.generate_weekly_report(txns, name)
            await context.bot.send_message(
                chat_id=int(chat_id_str),
                text=f"📊 *LAPORAN MINGGUAN dari {BOT_NAME}* 📊\n\n{report}",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Weekly report failed for {chat_id_str}: {e}")


async def invest_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 5:
        await update.message.reply_text(
            f"Cara pakai: `/invest <akun> <jenis> <nama> <lot> <harga_beli> [broker] [ket]`\n\n"
            f"Akun: 1 / 2 / 3\n"
            f"Contoh: `/invest 1 saham BBCA 100 8500 RTI beli pagi`\n"
            f"Jenis: saham, reksadana, obligasi, crypto, emas",
            parse_mode="Markdown",
        )
        return
    akun_no = args[0]
    if akun_no not in ("1", "2", "3"):
        await update.message.reply_text("Akun harus 1, 2, atau 3!")
        return
    sheet_name = f"Account{akun_no}"
    jenis, nama, lot_str, harga_str = args[1], args[2], args[3], args[4]
    try:
        lot = float(lot_str.replace(",", ""))
        harga = float(harga_str.replace(",", ""))
    except ValueError:
        await update.message.reply_text("Lot dan harga harus angka ya!")
        return
    total = int(lot * harga)
    broker = args[5] if len(args) > 5 else "-"
    ket = " ".join(args[6:]) if len(args) > 6 else "-"
    mgr = get_manager("investasi", sheet_name)
    mgr.append_row({
        "Tanggal": now_wib().strftime("%Y-%m-%d"),
        "Jenis": jenis, "Nama": nama, "Jumlah Lot": lot,
        "Harga Beli": harga, "Total": total, "Broker": broker, "Keterangan": ket,
    })
    await update.message.reply_text(
        f"✅ *Investasi Tercatat di Account {akun_no}!*\n"
        f"{nama} ({jenis}) — {lot} lot x {rp(harga)} = {rp(total)}\n"
        f"Broker: {broker}", parse_mode="Markdown",
    )


async def dividen_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 3:
        await update.message.reply_text(
            f"Cara pakai: `/dividen <akun> <nama_saham> <jumlah> [broker] [ket]`\n\n"
            f"Akun: 1 / 2 / 3\n"
            f"Contoh: `/dividen 1 BBCA 125000 RTI dividen Q2`",
            parse_mode="Markdown",
        )
        return
    akun_no = args[0]
    if akun_no not in ("1", "2", "3"):
        await update.message.reply_text("Akun harus 1, 2, atau 3!")
        return
    sheet_name = f"Account{akun_no}"
    nama, jml_str = args[1], args[2]
    try:
        jml = float(jml_str.replace(",", ""))
    except ValueError:
        await update.message.reply_text("Jumlah harus angka ya!")
        return
    broker = args[3] if len(args) > 3 else "-"
    ket = " ".join(args[4:]) if len(args) > 4 else "-"
    mgr = get_manager("investasi", sheet_name)
    mgr.append_row({
        "Tanggal": now_wib().strftime("%Y-%m-%d"),
        "Nama": nama, "Jumlah Lot": "", "Harga Beli": "",
        "Total": jml, "Broker": broker, "Keterangan": f"Dividen — {ket}",
    })
    await update.message.reply_text(
        f"💰 *Dividen Tercatat di Account {akun_no}!*\n{nama} — {rp(jml)}\nBroker: {broker}",
        parse_mode="Markdown",
    )


async def jual_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 6:
        await update.message.reply_text(
            f"Cara pakai: `/jual <akun> <jenis> <nama> <lot> <harga_beli> <harga_jual> [broker]`\n\n"
            f"Akun: 1 / 2 / 3\n"
            f"Contoh: `/jual 1 saham BBCA 100 8500 9200 RTI`",
            parse_mode="Markdown",
        )
        return
    akun_no = args[0]
    if akun_no not in ("1", "2", "3"):
        await update.message.reply_text("Akun harus 1, 2, atau 3!")
        return
    sheet_name = f"Account{akun_no}"
    jenis, nama, lot_str, hb_str, hj_str = args[1], args[2], args[3], args[4], args[5]
    try:
        lot = float(lot_str.replace(",", ""))
        hb = float(hb_str.replace(",", ""))
        hj = float(hj_str.replace(",", ""))
    except ValueError:
        await update.message.reply_text("Semua angka harus valid ya!")
        return
    pl = int((hj - hb) * lot)
    broker = args[6] if len(args) > 6 else "-"
    mgr = get_manager("investasi", sheet_name)
    mgr.append_row({
        "Tanggal": now_wib().strftime("%Y-%m-%d"),
        "Jenis": jenis, "Nama": nama, "Jumlah Lot": -lot,
        "Harga Beli": hb, "Total": int(lot * hj), "Broker": broker,
        "Keterangan": f"Jual — Profit/Loss: {rp(pl)}",
    })
    emoji = "🟢" if pl >= 0 else "🔴"
    await update.message.reply_text(
        f"{emoji} *Realisasi Tercatat di Account {akun_no}!*\n{nama} — {lot} lot\n"
        f"Beli: {rp(hb)} → Jual: {rp(hj)}\n"
        f"Profit/Loss: {rp(pl)}", parse_mode="Markdown",
    )


async def utang_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            f"Cara pakai: `/utang <nama> <jumlah> [jatuh_tempo] [ket]`\n\n"
            f"Contoh: `/utang John 500000 2026-07-15 pinjam buat beli laptop`",
            parse_mode="Markdown",
        )
        return
    nama = args[0]
    try:
        jml = float(args[1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Jumlah harus angka!")
        return
    jt = args[2] if len(args) > 2 else "-"
    ket = " ".join(args[3:]) if len(args) > 3 else "-"
    mgr = get_manager("utang", "Calculator")
    mgr.append_row({
        "Tanggal": now_wib().strftime("%Y-%m-%d"),
        "Nama": nama, "Jumlah": jml, "Status": "Belum Lunas",
        "Jatuh Tempo": jt, "Keterangan": ket,
    })
    await update.message.reply_text(
        f"📋 *Utang Tercatat!*\n{nama} — {rp(jml)}\nJatuh tempo: {jt}",
        parse_mode="Markdown",
    )


async def piutang_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            f"Cara pakai: `/piutang <nama> <jumlah> [jatuh_tempo] [ket]`\n\n"
            f"Contoh: `/piutang John 500000 2026-07-15 pinjamkan buat beli laptop`",
            parse_mode="Markdown",
        )
        return
    nama = args[0]
    try:
        jml = float(args[1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Jumlah harus angka!")
        return
    jt = args[2] if len(args) > 2 else "-"
    ket = " ".join(args[3:]) if len(args) > 3 else "-"
    mgr = get_manager("utang", "Calculator")
    mgr.append_row({
        "Tanggal": now_wib().strftime("%Y-%m-%d"),
        "Nama": nama, "Jumlah": jml, "Status": "Belum Diterima",
        "Jatuh Tempo": jt, "Keterangan": ket,
    })
    await update.message.reply_text(
        f"📋 *Piutang Tercatat!*\n{nama} — {rp(jml)}\nJatuh tempo: {jt}",
        parse_mode="Markdown",
    )


async def goal_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 3:
        await update.message.reply_text(
            f"Cara pakai: `/goal <nama_goal> <target_jumlah> <deadline> [ket]`\n\n"
            f"Contoh: `/goal 'Motor Baru' 15000000 2026-12-31 tabungan motor`",
            parse_mode="Markdown",
        )
        return
    try:
        target = float(args[1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Target jumlah harus angka!")
        return
    deadline = args[2]
    ket = " ".join(args[3:]) if len(args) > 3 else "-"
    mgr = get_manager("keuangan", "Goals")
    mgr.append_row({
        "Nama Goal": args[0], "Target Jumlah": target, "Terkumpul": 0,
        "Deadline": deadline, "Status": "Aktif", "Keterangan": ket,
    })
    await update.message.reply_text(
        f"🎯 *Goal Baru!*\n{args[0]} — Target: {rp(target)}\nDeadline: {deadline}",
        parse_mode="Markdown",
    )


async def tabung_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            f"Cara pakai: `/tabung <nama_goal> <jumlah>`\n\n"
            f"Contoh: `/tabung 'Motor Baru' 2500000`",
            parse_mode="Markdown",
        )
        return
    nama_goal = args[0]
    try:
        jml = float(args[1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Jumlah harus angka!")
        return
    mgr_goals = get_manager("keuangan", "Goals")
    rows = mgr_goals.get_all_rows()
    goal = next((r for r in rows if r.get("Nama Goal") == nama_goal), None)
    if not goal:
        await update.message.reply_text(f"Goal '{nama_goal}' nggak ketemu nih. Cek dulu ya!")
        return
    try:
        terkumpul = float(goal.get("Terkumpul", 0)) + jml
    except ValueError:
        terkumpul = jml
    mgr_prog = get_manager("keuangan", "Progress")
    mgr_prog.append_row({
        "Tanggal": now_wib().strftime("%Y-%m-%d"),
        "Nama Goal": nama_goal, "Jumlah Masuk": jml, "Saldo Goal": terkumpul,
    })
    await update.message.reply_text(
        f"💰 *Tabungan Masuk!*\n{nama_goal} +{rp(jml)}\n"
        f"Total terkumpul: {rp(terkumpul)}", parse_mode="Markdown",
    )


async def aset_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    args = context.args
    if not args or len(args) < 3:
        await update.message.reply_text(
            f"Cara pakai: `/aset <nama> <jenis> <nilai_beli> [nilai_sekarang] [ket]`\n\n"
            f"Contoh: `/aset 'iPhone 15' Elektronik 15000000 14000000 hp baru`",
            parse_mode="Markdown",
        )
        return
    nama, jenis = args[0], args[1]
    try:
        nilai_beli = float(args[2].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Nilai beli harus angka!")
        return
    nilai_now = float(args[3].replace(",", "")) if len(args) > 3 else nilai_beli
    ket = " ".join(args[4:]) if len(args) > 4 else "-"
    mgr = get_manager("keuangan", "Aset")
    mgr.append_row({
        "Nama Aset": nama, "Jenis": jenis, "Nilai Beli": nilai_beli,
        "Nilai Sekarang": nilai_now, "Tanggal Beli": now_wib().strftime("%Y-%m-%d"),
        "Keterangan": ket,
    })
    await update.message.reply_text(
        f"🏠 *Aset Tercatat!*\n{nama} ({jenis})\nBeli: {rp(nilai_beli)}\nSekarang: {rp(nilai_now)}",
        parse_mode="Markdown",
    )


async def list_sheets_cmd(update, context):
    name = fname(update.effective_user)
    _register(update.effective_user, update.effective_chat.id)
    lines = [f"📊 *Spreadsheet yang tersedia:*\n"]
    for key, spec in list_spreadsheets():
        lines.append(f"\n*{key}* — `{spec['name']}`")
        for sh in list_sheets(key):
            lines.append(f"  • {sh}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def post_init(app):
    commands = [
        BotCommand("start", "Mulai bot Oliv"),
        BotCommand("help", "Bantuan & daftar perintah"),
        BotCommand("pengeluaran", "Catat pengeluaran manual"),
        BotCommand("pemasukan", "Catat pemasukan manual"),
        BotCommand("ringkasan", "Ringkasan keuangan"),
        BotCommand("saldo", "Cek saldo semua akun"),
        BotCommand("hariini", "Pengeluaran hari ini"),
        BotCommand("mingguini", "7 hari terakhir"),
        BotCommand("terbesar", "Top 10 pengeluaran"),
        BotCommand("analisa", "Analisa pola keuangan"),
        BotCommand("budget", "Status budget bulan ini"),
        BotCommand("terakhir", "10 transaksi terakhir"),
        BotCommand("tanya", "Tanya Oliv soal keuangan"),
        BotCommand("invest", "Catat investasi/beli saham"),
        BotCommand("dividen", "Catat dividen diterima"),
        BotCommand("jual", "Catat jual investasi"),
        BotCommand("utang", "Catat utang"),
        BotCommand("piutang", "Catat piutang"),
        BotCommand("goal", "Buat target tabungan"),
        BotCommand("tabung", "Masukin dulu ke goal"),
        BotCommand("aset", "Catat pembelian aset"),
        BotCommand("sheets", "Lihat semua spreadsheet"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("Bot commands set.")


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not set.")

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start",        start))
    app.add_handler(CommandHandler("help",         help_cmd))
    app.add_handler(CommandHandler("pengeluaran",  pengeluaran))
    app.add_handler(CommandHandler("pemasukan",    pemasukan))
    app.add_handler(CommandHandler("ringkasan",    ringkasan))
    app.add_handler(CommandHandler("saldo",        saldo_cmd))
    app.add_handler(CommandHandler("hariini",      hariini_cmd))
    app.add_handler(CommandHandler("mingguini",    mingguini_cmd))
    app.add_handler(CommandHandler("terbesar",     terbesar_cmd))
    app.add_handler(CommandHandler("analisa",      analisa_cmd))
    app.add_handler(CommandHandler("budget",       budget_cmd))
    app.add_handler(CommandHandler("terakhir",     terakhir))
    app.add_handler(CommandHandler("tanya",        tanya))
    app.add_handler(CommandHandler("invest",       invest_cmd))
    app.add_handler(CommandHandler("dividen",      dividen_cmd))
    app.add_handler(CommandHandler("jual",         jual_cmd))
    app.add_handler(CommandHandler("utang",        utang_cmd))
    app.add_handler(CommandHandler("piutang",      piutang_cmd))
    app.add_handler(CommandHandler("goal",         goal_cmd))
    app.add_handler(CommandHandler("tabung",       tabung_cmd))
    app.add_handler(CommandHandler("aset",         aset_cmd))
    app.add_handler(CommandHandler("sheets",       list_sheets_cmd))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text))

    if app.job_queue:
        app.job_queue.run_daily(
            _send_weekly_report,
            time=dt_time(12, 0, 0),
            days=(6,),
            name="weekly_report",
        )
        logger.info("Weekly report scheduled: Sunday 19:00 WIB.")
    else:
        logger.warning("Job queue unavailable — install apscheduler.")

    logger.info("Bot started polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
    