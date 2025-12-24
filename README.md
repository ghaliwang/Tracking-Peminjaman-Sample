# Tracking-Peminjaman-Sample

Aplikasi desktop berbasis Python (Tkinter) untuk melakukan tracking peminjaman dan pengembalian sample QC.

Dikembangkan oleh **Team Final Quality Control - Penghancur Pintu Part 2**  
PT Langgeng Buana Jaya

---

## ✨ Fitur Utama
- Peminjaman & pengembalian sample
- Kamera capture dengan timestamp
- Preview data sebelum simpan
- History peminjaman lengkap + foto
- Pencarian realtime (Nama & Item#)
- Backup data (Excel + Foto) dengan proteksi password
- Single instance (aplikasi tidak bisa dibuka dua kali)
- Build ke `.exe` (Windows)

---

## 📂 Struktur File
- tracking_sample.py # main application
- item_list.xlsx # master item & nama (Pembantu auto complte)
- record_peminjaman.xlsx # database peminjaman (Bisa kosong karena auto generate)
- foto/ # foto pinjam & kembali
- logo_fqc.ico # icon aplikasi (Bisa ganti sesuai keinginan)


---

## 🛠️ Requirements

- Python **3.10+ (disarankan 3.11 / 3.13)**
- Windows OS (kamera & pywin32)

## Install dependency
```bash
pip install -r requirements.txt
```

## Menjalankan Aplikasi (Dev Mode)
python tracking_sample.py

## Build Menjadi .EXE
Pastikan sudah terinstall pyinstaller
```bash
pip install pyinstaller
```

Build:
```bash
pyinstaller --onefile --windowed --icon=logo_fqc.ico tracking_sample.py
```