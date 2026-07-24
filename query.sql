CREATE DATABASE lima
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; --utf8mb4 buat support emoji, unicode, dan karakter multibahasa 
-- kalo utf8mb4_unicode_ci bisa support sorting dan perbandingan karakter multibahasa, misal huruf a dengan á dianggap sama, huruf a dengan b dianggap beda, dsb
USE lima;

CREATE TABLE akun (
  id INT AUTO_INCREMENT PRIMARY KEY, 
  nomor_rekening VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(150) NOT NULL UNIQUE,
  no_hp VARCHAR(20) NOT NULL UNIQUE, 
  pin VARCHAR(255) NOT NULL,            -- simpennya pake bentuk hash (werkzeug) biar ga kebaca , maksimal 6 digit
  balance DECIMAL(15,2) NOT NULL DEFAULT 0,
  dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- timestampt buat waktunya kapan 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- InnoDB buat support foreign key, utf8mb4 buat support emoji, unicode, dan karakter multibahasa, utf8mb4_unicode_ci buat support sorting dan perbandingan karakter multibahasa


CREATE TABLE riwayat_transaksi (
  id INT AUTO_INCREMENT PRIMARY KEY,
  akun_id INT NOT NULL,
  jenis ENUM('deposit', 'withdraw', 'transfer_masuk', 'transfer_keluar') NOT NULL,
  jumlah DECIMAL(15,2) NOT NULL,
  saldo_setelah DECIMAL(15,2) NOT NULL,
  catatan VARCHAR(255) NULL,            -- keterangan buat apa transaksi ini 
  rekening_terkait VARCHAR(20) NULL,    -- khusus buat transfer: nomor rekening lawan transaksi
  waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (akun_id) REFERENCES akun(id) ON DELETE CASCADE -- kalo akun dihapus, semua riwayat transaksinya juga ikut dihapus 
  -- foreign key buat ngehubungin tabel riwayat_transaksi sama tabel akun, jadi kalo akun dihapus, semua riwayat transaksinya juga ikut dihapus
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- sama kayak di atas