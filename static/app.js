// Utilitas bersama untuk seluruh halaman (konvensional, tanpa framework/bundler)

let toastTimer = null; // timer untuk sembunyikan toast otomatis

function showToast(message, type = '') { // tampilkan pesan singkat (toast)
  const toast = document.getElementById('toast'); // ambil elemen toast
  if (!toast) return; // keluar bila elemen tidak ada
  toast.textContent = message; // set teks pesan
  toast.className = 'toast show' + (type ? ' ' + type : ''); // tambahkan kelas untuk tampil dan tipe
  clearTimeout(toastTimer); // hentikan timer lama bila ada
  toastTimer = setTimeout(() => { // mulai timer untuk sembunyikan toast
    toast.className = 'toast'; // kembalikan kelas default (sembunyikan)
  }, 3200); // tunggu 3.2 detik sebelum sembunyikan
}

async function handleLogin(event) {
  event.preventDefault();
  
  const identifier = document.getElementById('loginIdentifier').value.trim();
  const pin = document.getElementById('loginPin').value.trim();

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        identifier: identifier,
        pin: pin
      }),
    });

    const result = await response.json();

    if (result.ok) {
      window.location.href = '/dashboard';
    } else {
      alert(result.error || 'Login gagal.');
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Terjadi kesalahan jaringan.');
  }
}
