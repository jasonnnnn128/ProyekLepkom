import os
import random
import string
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Flask, jsonify, request, session, render_template, redirect
from werkzeug.security import generate_password_hash, check_password_hash # untuk hashing password biar ga kebaca di database

try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env') #ambil path file .env di folder yang sama dengan app.py
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

# Install aplikasi Flask dulu mas
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY',) #ambil secret key 

# konfigur dulu koneksi database MySQL
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', ''),
    'user': os.environ.get('DB_USER', ''), 
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', ''), 
}


# Buka koneksi database setiap kali dibutuhkan 
def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# Buat nomor rekening acak 10 digit buat user baru
def generate_nomor_rekening():
    return ''.join(random.choices(string.digits, k=10))


class BankAccount:

    def __init__(self, id_akun, nomor_rekening, name, balance):
        self.id_akun = id_akun
        self.nomor_rekening = nomor_rekening
        self.name = name
        self.balance = balance

    # Tambah saldo dan catat transaksi
    def deposit(self, amount, catatan=''):
        if amount <= 0:
            return False, "Jumlah deposit harus lebih dari 0"

        self.balance += amount #buat update saldo di database
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "UPDATE akun SET balance=%s WHERE id=%s", #buat
                (self.balance, self.id_akun)
            )
            cursor.execute(
                "INSERT INTO riwayat_transaksi (akun_id, jenis, jumlah, saldo_setelah, catatan) " #buat catat riwayat transaksi
                "VALUES (%s, 'deposit', %s, %s, %s)",
                (self.id_akun, amount, self.balance, catatan)
            )
            db.commit()
        finally:
            cursor.close()
            db.close()

        return True, f"Deposit berhasil: {amount}"

    # Kurangi saldo jika mencukupi
    def withdraw(self, amount, catatan=''):
        if amount <= 0:
            return False, "Jumlah penarikan harus lebih dari 0"
        if amount > self.balance:
            return False, "Saldo tidak mencukupi"

        self.balance -= amount
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "UPDATE akun SET balance=%s WHERE id=%s",
                (self.balance, self.id_akun)
            )
            cursor.execute(
                "INSERT INTO riwayat_transaksi (akun_id, jenis, jumlah, saldo_setelah, catatan) "
                "VALUES (%s, 'withdraw', %s, %s, %s)",
                (self.id_akun, amount, self.balance, catatan)
            )
            db.commit()
        finally:
            cursor.close()
            db.close()

        return True, f"Withdraw berhasil: {amount}"

    # Transfer saldo ke rekening lain 
    def transfer(self, nomor_rekening_tujuan, amount, catatan=''):
        if amount <= 0:
            return False, "Jumlah transfer harus lebih dari 0"
        if amount > self.balance:
            return False, "Saldo tidak mencukupi"
        if nomor_rekening_tujuan == self.nomor_rekening:
            return False, "Tidak bisa transfer ke rekening sendiri"

        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, name, balance FROM akun WHERE nomor_rekening=%s FOR UPDATE",
                (nomor_rekening_tujuan,)
            )
            tujuan = cursor.fetchone() #cursor fetchone() buat ambil satu baris data dari hasil query, kalo ada data yg sama return True
            if not tujuan:
                db.rollback()
                return False, "Nomor rekening tujuan tidak ditemukan"

            cursor.execute(
                "SELECT balance FROM akun WHERE id=%s FOR UPDATE",
                (self.id_akun,)
            )
            pengirim = cursor.fetchone()
            saldo_sekarang = pengirim['balance']

            if amount > saldo_sekarang:
                db.rollback() 
                return False, "Saldo tidak mencukupi"

            saldo_pengirim_baru = saldo_sekarang - amount
            saldo_penerima_baru = tujuan['balance'] + amount

            cursor.execute(
                "UPDATE akun SET balance=%s WHERE id=%s",
                (saldo_pengirim_baru, self.id_akun)
            )
            cursor.execute(
                "UPDATE akun SET balance=%s WHERE id=%s",
                (saldo_penerima_baru, tujuan['id'])
            )
            cursor.execute(
                "INSERT INTO riwayat_transaksi "
                "(akun_id, jenis, jumlah, saldo_setelah, catatan, rekening_terkait) "
                "VALUES (%s, 'transfer_keluar', %s, %s, %s, %s)",
                (self.id_akun, amount, saldo_pengirim_baru, catatan, nomor_rekening_tujuan)
            )
            cursor.execute(
                "INSERT INTO riwayat_transaksi "
                "(akun_id, jenis, jumlah, saldo_setelah, catatan, rekening_terkait) "
                "VALUES (%s, 'transfer_masuk', %s, %s, %s, %s)",
                (tujuan['id'], amount, saldo_penerima_baru, catatan, self.nomor_rekening)
            )
            db.commit()
            self.balance = saldo_pengirim_baru
        except Exception: #buat rollback kalo ada error 
            db.rollback()
            raise
        finally:
            cursor.close()
            db.close()

        return True, f"Transfer berhasil ke {tujuan['name']} ({nomor_rekening_tujuan})"

    def get_balance(self):
        return self.balance

    def to_dict(self): #buat convert data akun ke dictionary biar gampang di JSON
        return {
            'id_akun': self.id_akun,
            'nomor_rekening': self.nomor_rekening,
            'name': self.name,
            'balance': float(self.balance),
        }


#Bikin akun baru trus distore ke database
def create_account(name, email, no_hp, pin, balance):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM akun WHERE name=%s", (name,))
        if cursor.fetchone(): 
            return False, "Nama sudah terdaftar!", None

        cursor.execute("SELECT * FROM akun WHERE email=%s", (email,))
        if cursor.fetchone():
            return False, "Email sudah terdaftar!", None

        cursor.execute("SELECT * FROM akun WHERE no_hp=%s", (no_hp,))
        if cursor.fetchone():
            return False, "Nomor HP sudah terdaftar!", None

        nomor_rekening = generate_nomor_rekening() #buat generate nomor rekening acak 10 digit 
        pin_hash = generate_password_hash(pin) #buat hash pin biar ga kebaca di database

        cursor.execute(
            "INSERT INTO akun (nomor_rekening, name, email, no_hp, pin, balance) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nomor_rekening, name, email, no_hp, pin_hash, balance)
        )
        db.commit()
        return True, "Akun berhasil dibuat!", nomor_rekening
    finally:
        cursor.close()
        db.close()


#login pake nomor rekening, email, atau nomor HP bersama PIN
def login_account(identifier, pin):
    identifier = (identifier or '').strip()
    if '@' in identifier:
        identifier = identifier.lower()

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM akun WHERE nomor_rekening=%s OR email=%s OR no_hp=%s",
            (identifier, identifier, identifier)
        )
        result = cursor.fetchone()

        if not result or not check_password_hash(result['pin'], pin):
            return None #buat return None kalo identitas atau pin salah

        return BankAccount(
            result['id'],
            result['nomor_rekening'],
            result['name'],
            result['balance'],
        )
    finally:
        cursor.close()
        db.close()


#Balikin data akun berdasarkan ID
def load_account_by_id(id_akun):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM akun WHERE id=%s", (id_akun,))
        result = cursor.fetchone()
        if not result:
            return None
        return BankAccount(result['id'], result['nomor_rekening'], result['name'], result['balance'])
    finally:
        cursor.close()
        db.close()
        

#Ambil riwayat transaksi akun
def get_riwayat(id_akun, limit=20):
    db = get_db()
    cursor = db.cursor(dictionary=True) #uat cursor dictionary biar hasil query bisa diakses pake nama kolom
    try:
        cursor.execute(
            "SELECT jenis, jumlah, saldo_setelah, catatan, rekening_terkait, waktu "
            "FROM riwayat_transaksi WHERE akun_id=%s ORDER BY waktu DESC LIMIT %s", #buat ambil data riwayat transaksi berdasarkan id akun, diurutkan dari yang terbaru, dibatasi 20 data
            (id_akun, limit)
        )
        rows = cursor.fetchall() #buat ambil semua data hasil query
        for r in rows:
            r['jumlah'] = float(r['jumlah'])
            r['saldo_setelah'] = float(r['saldo_setelah'])
            r['waktu'] = r['waktu'].strftime('%d %b %Y, %H:%M')
        return rows
    finally:
        cursor.close()
        db.close()


#ngubbah jumlah input menjadi Decimal
def parse_amount(raw):
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, TypeError):
        return None
    if amount <= 0:
        return None
    return amount

# Halaman login utama
@app.route('/')
def halaman_login():
    if 'id_akun' in session:
        return redirect('/dashboard') #buat redirect ke halaman dashboard kalo udah login
    return render_template('index.html')


# Halaman dashboard setelah login
@app.route('/dashboard')
def halaman_dashboard():
    if 'id_akun' not in session:
        return redirect('/') #buat redirect ke halaman login kalo belum login
    return render_template('dashboard.html')

# API buat akun baru
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip() #strip() buat hapus spasi di awal dan akhir string, lower() buat bikin huruf kecil semua
    email = (data.get('email') or '').strip().lower() #lower() buat bikin huruf kecil semua
    no_hp = (data.get('no_hp') or '').strip() 
    pin = (data.get('pin') or '').strip()

    if not name or not email or not no_hp or not pin:
        return jsonify({'ok': False, 'error': 'Nama, email, nomor HP, dan PIN wajib diisi.'}), 400

    if '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'ok': False, 'error': 'Format email tidak valid.'}), 400

    if not no_hp.isdigit() or len(no_hp) < 9 or len(no_hp) > 15:
        return jsonify({'ok': False, 'error': 'Nomor HP tidak valid (9-15 digit angka).'}), 400

    if not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
        return jsonify({'ok': False, 'error': 'PIN harus 4-6 digit angka.'}), 400

    ok, message, nomor_rekening = create_account(name, email, no_hp, pin, Decimal('0'))
    if not ok:
        return jsonify({'ok': False, 'error': message}), 400

    return jsonify({'ok': True, 'message': message, 'nomor_rekening': nomor_rekening})


# API buat login akun
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get('identifier') or '').strip()
    pin = (data.get('pin') or '').strip()

    account = login_account(identifier, pin)
    if not account:
        return jsonify({'ok': False, 'error': 'Identitas atau PIN salah.'}), 401

    session['id_akun'] = account.id_akun
    return jsonify({'ok': True, 'account': account.to_dict()})


# API buat logout akun
@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'ok': True})


#API buat ambil data akun yang lagi login sama riwayat transaksinya
@app.route('/api/me', methods=['GET']) #kenapa pake /me? karena ini buat ambil data akun yang lagi login, jadi /me itu singkatan dari user
def api_me():
    if 'id_akun' not in session:
        return jsonify({'ok': False, 'error': 'Belum login.'}), 401

    account = load_account_by_id(session['id_akun'])
    if not account:
        session.clear()
        return jsonify({'ok': False, 'error': 'Akun tidak ditemukan.'}), 404

    return jsonify({
        'ok': True,
        'account': account.to_dict(),
        'riwayat': get_riwayat(account.id_akun),
    })


# API buat deposit saldo
@app.route('/api/deposit', methods=['POST'])
def api_deposit():
    if 'id_akun' not in session:
        return jsonify({'ok': False, 'error': 'Belum login.'}), 401

    data = request.get_json(silent=True) or {}
    amount = parse_amount(data.get('amount')) #parse_amount buat ubah jumlah input jadi Decimal, kalo ga valid return None
    catatan = (data.get('catatan') or '').strip()[:255]
    if amount is None:
        return jsonify({'ok': False, 'error': 'Jumlah deposit tidak valid.'}), 400

    account = load_account_by_id(session['id_akun'])
    ok, message = account.deposit(amount, catatan)
    if not ok:
        return jsonify({'ok': False, 'error': message}), 400

    return jsonify({'ok': True, 'message': message, 'account': account.to_dict()})


# API buat tarik saldo
@app.route('/api/withdraw', methods=['POST'])
def api_withdraw():
    if 'id_akun' not in session:
        return jsonify({'ok': False, 'error': 'Belum login.'}), 401

    data = request.get_json(silent=True) or {}
    amount = parse_amount(data.get('amount')) #parse_amount buat ubah jumlah input jadi Decimal, kalo ga valid return None
    catatan = (data.get('catatan') or '').strip()[:255]
    if amount is None:
        return jsonify({'ok': False, 'error': 'Jumlah penarikan tidak valid.'}), 400

    account = load_account_by_id(session['id_akun'])
    ok, message = account.withdraw(amount, catatan)
    if not ok:
        return jsonify({'ok': False, 'error': message}), 400

    return jsonify({'ok': True, 'message': message, 'account': account.to_dict()})


# APIbuat transfer saldo ke rekening lain
@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    if 'id_akun' not in session:
        return jsonify({'ok': False, 'error': 'Belum login.'}), 401

    data = request.get_json(silent=True) or {}
    nomor_tujuan = (data.get('nomor_rekening_tujuan') or '').strip() 
    amount = parse_amount(data.get('amount'))
    catatan = (data.get('catatan') or '').strip()[:255]

    if not nomor_tujuan:
        return jsonify({'ok': False, 'error': 'Nomor rekening tujuan wajib diisi.'}), 400
    if amount is None:
        return jsonify({'ok': False, 'error': 'Jumlah transfer tidak valid.'}), 400

    account = load_account_by_id(session['id_akun'])
    ok, message = account.transfer(nomor_tujuan, amount, catatan)
    if not ok:
        return jsonify({'ok': False, 'error': message}), 400

    return jsonify({'ok': True, 'message': message, 'account': account.to_dict()})


#buat ngerun aplikasi Flask di server, bisa diakses dari jaringan lokal pake router wifi yang sama
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # ini untuk menjalankan aplikasi di server, 
    #bisa diakses dari jaringan lokal pake router wifi yang sama

    #app.run(debug=True, port=5000) #buatlocalhost cuma bisa di laptop atau device sendiri 
