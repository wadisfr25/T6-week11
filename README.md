# T6 Week 11 - Post Manager App

Tugas ini merupakan aplikasi desktop Python menggunakan **PySide6** untuk mengelola data post melalui **REST API**. Aplikasi menerapkan **multi-threading** menggunakan `QThreadPool` dan `QRunnable` agar proses request API tetap berjalan tanpa membuat antarmuka membeku.

## Fitur Singkat

- Menampilkan daftar post dari API
- Melihat detail post beserta komentar
- Menambahkan post baru
- Mengubah data post
- Menghapus post
- Menampilkan status loading dan pesan error jika request gagal

## Teknologi yang Digunakan

- Python
- PySide6
- REST API
- QThreadPool / QRunnable

## Cara Menjalankan

1. Pastikan Python sudah terpasang.
2. Install dependency:

```bash
pip install PySide6
```

3. Jalankan program:

```bash
python post_manager.py
```

## Screenshot Hasil

![Screenshot aplikasi](image.png)
