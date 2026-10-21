document.addEventListener("DOMContentLoaded", function() {
    // 1. Konfirmasi Logout
    // Pastikan tombol atau tautan logout Anda memiliki id="logoutBtn" di HTML
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            Swal.fire({
                title: 'Apakah Anda yakin?',
                text: "Anda akan keluar dari sistem.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Ya, Logout!',
                cancelButtonText: 'Batal'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = href;
                }
            });
        });
    }
});

// 2. Fungsi Hapus Data (Gunakan onclick="deleteData('id_review')" pada tombol hapus)
window.deleteData = function(reviewId) {
    Swal.fire({
        title: 'Hapus Data?',
        text: "Data ulasan yang dihapus tidak dapat dikembalikan!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Ya, Hapus!',
        cancelButtonText: 'Batal'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/delete_data/${reviewId}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({ title: 'Terhapus!', html: data.message, icon: 'success' }).then(() => location.reload());
                    } else {
                        Swal.fire({ title: 'Gagal!', html: data.message, icon: 'error' });
                    }
                })
                .catch(err => Swal.fire('Error', 'Terjadi kesalahan sistem saat menghapus data', 'error'));
        }
    });
}

// 3. Fungsi Upload CSV (Panggil fungsi ini saat form disubmit)
window.submitUploadCSV = function(formElement) {
    const formData = new FormData(formElement);
    Swal.fire({
        title: 'Sedang Mengunggah...',
        text: 'Mohon tunggu sementara data sedang diproses ke database.',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    fetch('/upload_csv', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.saved_count === 0) {
                    Swal.fire({ title: 'Selesai', html: data.message, icon: 'info' }).then(() => location.reload());
                } else {
                    Swal.fire({ title: 'Berhasil!', html: data.message, icon: 'success' }).then(() => location.reload());
                }
            } else {
                Swal.fire({ title: 'Gagal!', html: data.message, icon: 'error' });
            }
        })
        .catch(err => Swal.fire('Error', 'Gagal memproses data CSV.', 'error'));
}

// 4. Fungsi Penarikan Data (Scraping)
window.triggerScraping = function(formElement) {
    const formData = new FormData(formElement);
    const payloadData = Object.fromEntries(formData.entries());
    Swal.fire({
        title: 'Menarik Data (Scraping)...',
        text: 'Proses ini mungkin membutuhkan waktu, mohon jangan tutup halaman ini.',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    fetch('/trigger_scraping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.saved_count === 0) {
                Swal.fire({ title: 'Selesai', html: data.message, icon: 'info' }).then(() => location.reload());
            } else {
                Swal.fire({ title: 'Penarikan Selesai!', html: data.message, icon: 'success' }).then(() => location.reload());
            }
        } else {
            Swal.fire({ title: 'Gagal!', html: data.message, icon: 'error' });
        }
    })
    .catch(err => Swal.fire('Error', 'Gagal menghubungi server untuk penarikan data.', 'error'));
}

// 5. Fungsi Eksekusi Analisis (Model AI)
window.runAnalysis = function() {
    Swal.fire({
        title: 'Memproses Analisis AI...',
        text: 'Sedang menganalisis sentimen dan aspek data baru. Mohon tunggu.',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    fetch('/run-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({ title: 'Analisis Selesai!', html: data.message, icon: 'success' }).then(() => location.reload());
        } else {
            Swal.fire({ title: 'Gagal!', html: data.message, icon: 'error' });
        }
    })
    .catch(err => Swal.fire('Error', 'Gagal menghubungi server untuk analisis AI.', 'error'));
}