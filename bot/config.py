BOT_NAME = "Oliv"

# ── TIPE TRANSAKSI ─────────────────────────────────────────────
TIPE_PEMASUKAN  = "Pemasukan"
TIPE_PENGELUARAN = "Pengeluaran"

# ── AKUN (10 TOTAL) ────────────────────────────────────────────
DAFTAR_AKUN = [
    "Cash", "BCA", "GoPay", "ShopeePay", "DANA",
    "RDN", "Jago", "Tabungan", "Dana Darurat", "Investasi"
]

AKUN_KEYWORDS = {
    "GoPay":     ["gopay", "go-pay", "qr", "qris"],
    "ShopeePay": ["shopeepay", "shopee pay", "shopee"],
    "DANA":      ["dana"],
    "RDN":       ["rdn"],
    "BCA":       ["bca"],
    "Jago":      ["jago"],
    "Tabungan":  ["tabungan", "tabung"],
    "Dana Darurat": ["dana darurat", "darurat"],
    "Investasi": ["investasi", "invest"],
}

# ── KATEGORI PENGELUARAN (12) ──────────────────────────────────
EXPENSE_CATEGORIES = [
    "Makan & Minum",
    "Transportasi",
    "Pulsa / Internet",
    "Cicilan & Tagihan",
    "Hiburan & Lifestyle",
    "Tempat Tinggal (Housing)",
    "Kesehatan",
    "Belanja Pakaian & Barang",
    "Pendidikan",
    "Hadiah & Sosial",
    "Bisnis",
    "Lainya",
]

# ── INCOME CATEGORIES (5) ──────────────────────────────────────
INCOME_CATEGORIES = [
    "Gaji",
    "Bonus",
    "Dividen",
    "Usaha",
    "Lain-lain",
]

# ── NON-BUDGET CATEGORIES ──────────────────────────────────────
NON_BUDGET_CATEGORIES = [
    "[Transfer]",
    "[Refund]",
    "[piutang]",
    "[Biaya Tak Terduga]",
    "[Dll]",
]

ALL_CATEGORIES = EXPENSE_CATEGORIES + INCOME_CATEGORIES + NON_BUDGET_CATEGORIES

# ── EMOJI KATEGORI ─────────────────────────────────────────────
KATEGORI_EMOJI = {
    "Makan & Minum": "🍽️",
    "Transportasi": "🚗",
    "Pulsa / Internet": "📡",
    "Cicilan & Tagihan": "📄",
    "Hiburan & Lifestyle": "🎮",
    "Tempat Tinggal (Housing)": "🏠",
    "Kesehatan": "💊",
    "Belanja Pakaian & Barang": "🛍️",
    "Pendidikan": "📚",
    "Hadiah & Sosial": "🎁",
    "Bisnis": "💼",
    "Lainya": "📌",
    "Gaji": "💰",
    "Bonus": "🎉",
    "Dividen": "📈",
    "Usaha": "🏪",
    "Lain-lain": "📎",
    "[Transfer]": "🔁",
    "[Refund]": "↩️",
    "[piutang]": "🤝",
    "[Biaya Tak Terduga]": "⚠️",
    "[Dll]": "📋",
}

# ── KOMENTAR PERSONAL ──────────────────────────────────────────
KOMENTAR_OLIV = {
    "rokok":        ["rokok lagi nih Zee 👀", "hati-hati ya Zee 🌿", "udah berapa batang hari ini? 😄"],
    "kopi":         ["kopi terus Zee ☕", "caffeine mode on 😂", "kopi pagi atau siang nih?"],
    "grab":         ["ojol maning 🛵", "kemana nih Zee?", "grab terus, kapan jalan kaki? 😄"],
    "gojek":        ["ojol lagi Zee 🛵", "ongkir atau pergi nih?"],
    "makan":        ["jangan lupa makan sehat juga ya 🥗", "enak ga? 😄"],
    "nasi":         ["makan siang nih? 🍚", "enak ga Zee?"],
    "bensin":       ["siap gaskeun! ⛽", "motor atau mobil nih?"],
    "shopee":       ["shopee lagi Zee 📦", "nunggu 'pesanan dikirim' nih hehe"],
    "tokopedia":    ["belanja online lagi 📦", "apa yang dibeli nih Zee?"],
    "kasih mamah":  ["baik banget Zee! 👩‍👧", "mamah pasti seneng 🤍"],
    "kasih bapak":  ["baik banget Zee! 👨‍👧", "bapak pasti seneng 🤍"],
    "nabung":       ["yeay nabung! 🎉 konsisten ya Zee", "duit masa depan nih 💪"],
    "investasi":    ["investor mode on! 📈💪", "cuan cuan cuan~"],
    "emas":         ["nabung emas, smart! ✨", "safe haven asset nih 💛"],
    "pulsa":        ["pulsa lagi Zee? 📱", "jangan lupa cek kuota ya"],
    "internet":     ["wifi atau data nih? 📡", "streaming mulu ya? 😂"],
    "listrik":      ["tagihan bulanan nih ⚡", "hemat listrik ya Zee"],
    "gaji":         ["yeay gajian! 🎉", "alhamdulillah ya Zee 💰"],
    "bonus":        ["rezeki nomplok! 🎊", "jangan lupa disyukuri ya"],
}

# ── SHEET HEADERS V4 ───────────────────────────────────────────
TRANSAKSI_HEADERS = ["Akun", "Tanggal", "Jam", "Payee", "Memo", "Tag", "Category", "Clr", "PAYMENT", "DEPOSIT"]

# ── FALLBACK KEYWORDS ────────────────────────────────────────────
FALLBACK_KEYWORDS = {
    "Makan & Minum": ["makan","minum","kopi","teh","nasi","bakso","mie","soto","ayam",
                      "cafe","resto","restoran","starbucks","kfc","mcdo","pizza","burger",
                      "jajan","snack","cemilan","es","minuman","makanan","warteg","warung",
                      "sarapan","boba","gorengan","seafood","rokok","sigaret","roti","donat"],
    "Transportasi":   ["bensin","bbm","grab","gojek","ojek","parkir","tol","busway","kereta",
                        "commuter","bus","angkot","taksi","pertalite","pertamax","oli",
                        "servis motor","servis mobil","cuci motor","ban","aki"],
    "Pulsa / Internet": ["pulsa","kuota","paket","internet","data","telkomsel","indosat",
                         "xl","smartfren","wifi","langganan"],
    "Cicilan & Tagihan": ["tagihan","listrik","air","gas","asuransi","cicilan","kredit",
                           "kartu kredit","angsuran"],
    "Hiburan & Lifestyle": ["bioskop","konser","teater","kafe","salon","spa","gym","fitness",
                            "olahraga","spotify","netflix","disney","gaming"],
    "Tempat Tinggal (Housing)": ["kosan","sewa","rumah","renovasi","pertukangan","cat","furniture"],
    "Kesehatan": ["obat","dokter","rumah sakit","klinik","apotek","vitamin","kesehatan","medical"],
    "Belanja Pakaian & Barang": ["baju","celana","sepatu","tas","pakaian","skincare","sabun",
                                  "sampo","elektronik","hp","charger","laptop","kamera",
                                  "uniqlo","h&m","zara"],
    "Pendidikan": ["sekolah","kuliah","les","kursus","buku","training","seminar","pendidikan"],
    "Hadiah & Sosial": ["mamah","mama","bapak","ayah","papa","adik","kakak","abang",
                        "kasih","kirimin","hadiah","kado","sedekah","donasi","infaq","zakat","traktir"],
    "Bisnis": ["bisnis","supplies","marketing","iklan","tools","fotografi","videografi"],
}
