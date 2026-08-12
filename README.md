# Bank Digital — Web App (HTML/CSS/JS + Python/Flask + MySQL)

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

## Instalasi dan cara ngerunnya

### 1. Yang di perluin
- Python 
- MySQL Server 

### 2. Buat database & tabel
- ada di query.sql

### 3. Atur kredensial database
export SECRET_KEY="kunci-rahasia-acak-anda"
export DB_HOST=host anda
export DB_USER=user anda
export DB_PASSWORD="password_mysql_anda"
export DB_NAME= nama db anda

> Kalo mau pake user khusus, buat dulu:
> `CREATE USER 'username'@'localhost' IDENTIFIED BY 'passwordnya';`
> `GRANT ALL PRIVILEGES ON databasenya.* TO 'username'@'localhost';`

### 4. Jalankan server
python app.py di terminal or run code

Buka `http://127.0.0.1:5000/` di browser untuk server lokal
atau alamat ip kalian jika menggunakan port (0.0.0.0)

## Alur Penggunaan

1. **Daftar Akun** — isi nama, PIN, dan saldo awal.
   Nomor rekening akan tampil setelah berhasil mendaftar
2. **Masuk** — login pakai nomor rekening & PIN yang sama.
3. Di **Dashboard**, kartu digital menampilkan saldo riwayat transaksi untuk setor tarik dan transfer
   Gunakan tombol **Setor / Deposit** atau **Tarik Tunai** untuk transaksi;
4. Tombol **Keluar** untuk logout.

## Endpoint API 

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/api/register` | Daftar akun baru |
| POST | `/api/login` | Login (membuat session) |
| POST | `/api/logout` | Logout (menghapus session) |
| GET | `/api/me` | Info akun aktif + riwayat transaksi |
| POST | `/api/deposit` | Setor dana |
| POST | `/api/withdraw` | Tarik dana |

