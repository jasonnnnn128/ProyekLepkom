# Bank Digital — Web App (HTML/CSS/JS + Python/Flask + MySQL)

Versi web dari `bank_sql_fix_banget.py`. Frontend memakai **HTML, CSS, dan
JavaScript murni** (tanpa framework/bundler seperti React atau Django
template). Backend memakai **Flask** (Python) sebagai lapisan API tipis —
logika transaksinya (class `BankAccount`, `create_account`, `login_account`,
`deposit`, `withdraw`) diadaptasi langsung dari skrip CLI yang Anda berikan.

## Update Terbaru (v3)

- **Tema tampilan baru**: putih + kuning + hitam, bergaya brutalist (border tebal, sudut tegas, bayangan solid) — sesuai referensi yang diberikan.
- **Login sekarang pakai Nomor Rekening + PIN**, bukan nama lagi.
- **Pendaftaran** kini butuh **Nama, Email, Nomor HP, dan PIN** (semua wajib, email & no HP harus unik).
- **PIN dibatasi maksimal 6 digit** — dibatasi dari sisi tampilan (tidak bisa mengetik lebih dari 6 karakter) **dan** divalidasi ulang di server (4-6 digit angka).

**Kalau database Anda sudah ada dari versi sebelumnya**, jalankan **`migration_v3.sql`** di MySQL Workbench (setelah `migration_v2.sql` kalau belum pernah dijalankan). Akun lama tetap bisa dipakai — cukup login pakai nomor rekening yang sudah didapat sebelumnya.

**Kalau baru mulai dari nol**, langsung pakai `schema.sql` (sudah termasuk semua kolom terbaru).

## Update Terbaru (v2)

- **Kode antrian dihapus**, diganti **nomor rekening** (10 digit acak) sebagai identitas akun.
- **Deposit & Withdraw** sekarang punya kolom **keterangan** (untuk apa transaksi itu dilakukan), tersimpan dan tampil di riwayat.
- **Fitur baru: Transfer antar rekening** — masukkan nomor rekening tujuan, sistem otomatis menampilkan nama pemiliknya, lalu transfer dana beserta keterangan. Tercatat di riwayat kedua akun (pengirim: "Transfer Keluar", penerima: "Transfer Masuk").

**Kalau database Anda sudah pernah dibuat dari `schema.sql` versi lama** (masih ada kolom `kode_antrian`), jangan jalankan `schema.sql` lagi — jalankan **`migration_v2.sql`** saja di MySQL Workbench. Ini akan mengubah struktur tabel tanpa menghapus data akun yang sudah ada.

**Kalau baru mulai dari nol**, langsung pakai `schema.sql` seperti biasa (sudah termasuk semua kolom baru).

## Apa yang berubah dari skrip asli

| Skrip CLI asli | Versi web ini |
|---|---|
| Menu `inquirer.select()` di terminal | Tombol & form HTML biasa |
| Login disimpan di variabel Python selama program jalan | Login disimpan di **session cookie** Flask, aman lintas request |
| PIN disimpan teks biasa di DB | PIN di-**hash** (werkzeug `generate_password_hash`) |
| Tidak ada riwayat transaksi | Ditambah tabel `riwayat_transaksi` + ditampilkan di dashboard |
| 1 koneksi DB global | Koneksi dibuka/ditutup per-request (lebih aman untuk banyak pengguna) |

Struktur data (`akun`: kode_antrian, name, pin, balance) dan alur fungsinya
(`generate_kode()`, `deposit()`, `withdraw()`, `get_balance()`) tetap sama
persis polanya dengan skrip asli.

## Struktur Folder

```
bank_app/
├── app.py                 # Backend Flask (adaptasi logika dari skrip asli)
├── requirements.txt
├── schema.sql              # CREATE TABLE akun & riwayat_transaksi
├── .env.example
├── templates/
│   ├── index.html          # Halaman login & daftar akun
│   └── dashboard.html      # Halaman saldo, setor/tarik, riwayat
└── static/
    ├── css/style.css       # Desain UI (tema kartu digital navy + mint)
    └── js/app.js           # Utilitas JS bersama (notifikasi toast)
```

## Instalasi & Menjalankan

### 1. Prasyarat
- Python 3.10+
- MySQL Server aktif

### 2. Install dependensi
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Buat database & tabel
```bash
mysql -u root -p < schema.sql
```
Ini akan membuat database `lima` beserta tabel `akun` dan `riwayat_transaksi`
(nama database sama seperti pada skrip asli Anda).

### 4. Atur kredensial database
```bash
export SECRET_KEY="kunci-rahasia-acak-anda"
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD="password_mysql_anda"
export DB_NAME=lima
```

> Jika memakai user MySQL khusus (disarankan, bukan root), buat dulu:
> `CREATE USER 'bankuser'@'localhost' IDENTIFIED BY 'passwordanda';`
> `GRANT ALL PRIVILEGES ON lima.* TO 'bankuser'@'localhost';`

### 5. Jalankan server
```bash
python app.py
```
Buka `http://127.0.0.1:5000/` di browser.

## Alur Penggunaan

1. **Daftar Akun** — isi nama, PIN (minimal 4 digit angka), dan saldo awal.
   Kode antrian akan tampil setelah berhasil.
2. **Masuk** — login pakai nama & PIN yang sama.
3. Di **Dashboard**, kartu digital menampilkan saldo & kode antrian Anda.
   Gunakan tombol **Setor / Deposit** atau **Tarik Tunai** untuk transaksi;
   saldo & riwayat transaksi ter-update otomatis tanpa reload halaman.
4. Tombol **Keluar** untuk logout.

## Endpoint API (dipanggil oleh app.js via `fetch`)

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/api/register` | Daftar akun baru |
| POST | `/api/login` | Login (membuat session) |
| POST | `/api/logout` | Logout (menghapus session) |
| GET | `/api/me` | Info akun aktif + riwayat transaksi |
| POST | `/api/deposit` | Setor dana |
| POST | `/api/withdraw` | Tarik dana |

## Catatan Produksi
- Set `debug=False` di `app.py` sebelum deploy.
- Jalankan lewat WSGI server seperti `gunicorn` (`gunicorn -w 4 app:app`), bukan `python app.py`.
- Gunakan HTTPS dan `SECRET_KEY` acak yang kuat.
- Pertimbangkan menaikkan panjang minimum PIN dan menambahkan rate-limit
  percobaan login untuk keamanan tambahan.
