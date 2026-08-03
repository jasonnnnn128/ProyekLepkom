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
