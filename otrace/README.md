# Otrace — Powerful Cybersecurity Suite (9router-safe)

Otrace adalah satu CLI yang menggabungkan 14 tools keamanan siber populer ke dalam
satu alur kerja yang konsisten, dengan jaminan **tidak mengganggu 9router** yang
berjalan di laptop ini.

## Tools terintegrasi

| Kategori | Tool |
|---|---|
| Recon | Nmap |
| Web | SQLmap, Nikto |
| Akses | OpenSSH |
| Vulnerability | OpenVAS, GVM |
| Password | John the Ripper, Hydra |
| Exploit | Metasploit |
| Wireless | Aircrack-ng |
| Network | Wireshark (tshark) |
| Forensics | Autopsy |
| Reverse | Ghidra, JADX |

## Prinsip isolasi 9router

1. **Port terlindung**: 443 (MITM) dan 20128 (app) tidak pernah di-bind / di-scan
   sebagai target; band 3000–8888 (cf-autopilot) juga dihindari.
2. **`/etc/hosts` tidak pernah ditulis** — entri 9router tetap intact.
3. **Tidak ada `pkill` pola luas**; hanya proses yang diluncurkan Otrace sendiri
   yang dapat dihentikan (melalui PID yang dicatat Otrace).
4. **Pre-flight & post-flight**: setiap perintah mengecek kesehatan 9router
   (`:20128/api/health`, `:_mitm_health`) dan entri hosts sebelum & sesudah jalan.
   Bila berubah → peringatan & exit code non-zero.
5. **Target 9router ditolak**: domain/IP/port yang terkait 9router otomatis
   diblokir oleh isolation guard.
6. **State terpisah**: `~/.otrace` (bukan `~/.9router`); tidak ada file yang
   ditulis ke direktori 9router.

## Instalasi

```bash
cd "/Volumes/MORVEXA-CLOUD/SHARED-DATA/iCloud-Drive/Free cloud Host"
chmod +x bin/otrace
./bin/otrace doctor
```

Opsional: symlink ke PATH:
```bash
ln -s "$(pwd)/bin/otrace" /usr/local/bin/otrace
```

## Penggunaan

```bash
otrace doctor                       # cek env & isolasi
otrace tools                        # daftar tool & status pasang
otrace scope --add 192.168.1.0/24  # daftarkan target yang Anda miliki izinnya
otrace scan 192.168.1.10           # pipeline nmap + nikto + sqlmap
otrace recon 192.168.1.10          # nmap saja
otrace web http://target            # nikto + sqlmap
otrace crack hashes.txt             # john
otrace reverse app.apk              # ghidra + jadx
otrace forensics disk.img          # autopsy (+ --pcap)
otrace wireless capture.cap        # aircrack-ng
otrace exploit --cmd "version; exit"  # metasploit
otrace vuln 192.168.1.10           # openvas/gvm
otrace report <run_id>             # tampilkan report
otrace isolate                     # cek isolasi 9router
```

## Scope / izin

Secara default Otrace **menolak** target yang tidak terdaftar di `~/.otrace/scope.txt`.
Tambahkan target yang Anda miliki / punya izin tertulis. Nonaktifkan dengan
`OTRACE_SCOPE_REQUIRED=0` di `~/.otrace/config.env`.

## Instalasi tool yang belum ada

Hanya `ssh` yang terdeteksi terpasang. Tool lain opsional; Otrace tetap jalan dan
menandai `not_installed` + petunjuk pasang. Contoh:
```bash
brew install nmap nikto hydra john aircrack-ng tshark jadx ghidra
pip3 install sqlmap
```

## Output

Setiap run tersimpan di `~/.otrace/runs/<run_id>/`:
- `report.json` — data terstruktur
- `report.md` — ringkasan markdown
- `<tool>.out` / `<tool>.err` — output mentah tiap tool

## Keamanan & etika

Gunakan hanya pada sistem yang Anda miliki atau punya izin tertulis. Otrace
menolak target 9router dan tidak akan menyentuh layanan lokal yang dilindungi.