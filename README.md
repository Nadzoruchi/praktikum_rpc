# Praktikum Mandiri RPC

Implementasi mengikuti kode dasar dan butir latihan pada modul praktikum. Folder `praktikum1_xmlrpc` memuat XML-RPC; `praktikum2_grpc` memuat kontrak Protobuf, server, dan client; `praktikum3_kegagalan` memuat skrip eksperimen retry, concurrency, throughput, dan failover.

## Persiapan

Gunakan Python 3.10 atau lebih baru. Dari folder proyek:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Untuk Linux/macOS, aktifkan dengan `source .venv/bin/activate`. Python XML-RPC ada di standard library; gRPC memerlukan `grpcio` dan `grpcio-tools`.

## Praktikum 1 - XML-RPC

Buka dua terminal di root proyek. Terminal pertama:

```powershell
python .\praktikum1_xmlrpc\server_kalkulator.py
```

Terminal kedua:

```powershell
python .\praktikum1_xmlrpc\client_kalkulator.py --xml-size --benchmark
```

Client mendemonstrasikan `tambah`, `kali`, `bagi`, `pangkat`, `akar`, `statistik`, bilangan lebih besar dari 2^31, dan nilai tanggal XML-RPC. Untuk L1.2, trace verbose hanya dinyalakan pada satu pemanggilan `statistik`, sehingga request `<methodCall>` dan response `<methodResponse>` memperlihatkan list/dictionary tanpa membanjiri terminal. Benchmark tetap menjalankan 100 panggilan RPC sungguhan, tetapi tanpa trace per panggilan agar durasi terminal tidak didominasi pencetakan output. Server mencatat request yang diterima. `--xml-size` mengukur byte body XML hasil serializer Python, dan menghitung payload sebagai dua digit operand (`5` dan `3`); definisi payload ini perlu dinyatakan saat melaporkan persentase overhead.

`datetime` dikirim sebagai tipe tanggal XML-RPC. Server menerima objek `xmlrpc.client.DateTime`, bukan `datetime.datetime` asli. XML-RPC standar membatasi integer ke signed 32-bit. `xmlrpc.client` Python menolak nilai seperti `2**40` dengan `OverflowError` saat marshalling, sebelum request dikirim; client menangkapnya agar latihan berikutnya tetap berjalan. Integer besar perlu dikirim sebagai string/representasi terpisah atau memakai format/protokol yang mendukungnya.

Benchmark `--benchmark` membandingkan 100 panggilan RPC dengan 100 operasi lokal. Hasil lokal sangat dipengaruhi interpreter/timer dan RPC mencakup latensi jaringan, sehingga laporkan waktu terukur, bukan angka universal. Jika server berhenti, client menangani kegagalan koneksi dengan pesan arahan.

Untuk dua komputer, jalankan server di komputer server, lalu ganti URL pada client:

```powershell
python .\praktikum1_xmlrpc\client_kalkulator.py --url http://IP_SERVER:8000/ --benchmark
```

Port 8000 harus dapat dijangkau di jaringan lokal.

## Praktikum 2 - gRPC dan Protocol Buffers

Generate stub sesudah mengubah `.proto`:

```powershell
python .\praktikum2_grpc\generate_stubs.py
```

Ini membuat `akademik_pb2.py` dan `akademik_pb2_grpc.py` di folder praktikum. Jalankan server dan client dari root:

```powershell
python .\praktikum2_grpc\server_grpc.py
python .\praktikum2_grpc\client_grpc.py
```

Server/client mencakup unary (`GetMahasiswa`, `TambahNilai`), server streaming (`StreamNilai`), client streaming (`KirimBanyakNilai`), dan bidirectional streaming (`Diskusi`). Client juga mengirim 10 pemanggilan unary dengan `.future()` lalu mengumpulkan hasil menggunakan `.result()`. Ruang diskusi meneruskan pesan ke client yang sedang terhubung pada ruang yang sama. Data dan deduplikasi disimpan di memori proses, jadi kembali ke nilai awal setelah server dimulai ulang.

Untuk L2.3, `prodi = 4` ditambahkan sebagai field opsional pada `Mahasiswa`. Protobuf mengabaikan field baru yang tidak dikenal oleh client lama, sehingga client lama tetap dapat membaca field bernomor 1-3. Jangan memakai ulang nomor field yang dihapus; tandai nomor/nama yang dihapus sebagai `reserved`. Client baru terhadap server lama membaca `prodi` sebagai nilai default string kosong.

L2.4 mencetak ukuran hasil `SerializeToString()` dan body XML-RPC dari nilai field yang sama. Ini ukuran payload serialisasi saja, bukan ukuran transfer penuh: HTTP/2, HTTP, framing Protobuf, dan header tidak disetarakan.

## Praktikum 3 - concurrency, timeout, dan toleransi kegagalan

Generate stub, kemudian jalankan server dengan simulasi balasan lambat:

```powershell
python .\praktikum2_grpc\generate_stubs.py
python .\praktikum2_grpc\server_grpc.py --slow-transfer
```

Di terminal lain jalankan 20 transfer dengan request ID yang tetap saat retry (L3.1):

```powershell
python .\praktikum3_kegagalan\eksperimen.py --count 20
```

Server mencatat respons per `request_id`. Timeout dapat muncul setelah saldo berubah; retry dengan ID sama mengambil hasil yang sudah dicatat. Saldo total harus 1500 dan saldo A berkurang 200 jika semua 20 transaksi berhasil. Untuk mengulang eksperimen, restart server agar saldo kembali ke nilai awal.

Untuk memperlihatkan efek ID baru pada setiap percobaan (L3.2), restart server dengan `--slow-transfer` lalu jalankan:

```powershell
python .\praktikum3_kegagalan\eksperimen.py --count 20 --new-id-per-retry
```

Retry yang memakai ID baru tidak dikenali sebagai duplikat. Karena server bisa sudah menerapkan transfer sebelum balasan terlambat melewati deadline, percobaan ulang dapat menerapkan operasi yang sama lagi. Hasil angka bergantung pada pengacakan delay dan waktu eksekusi; catat saldo aktual.

Untuk L3.3, restart server dengan lock dimatikan pada jalur transfer:

```powershell
python .\praktikum2_grpc\server_grpc.py --unsafe-transfer
python .\praktikum3_kegagalan\eksperimen.py --count 50 --unsafe
```

Bandingkan total saldo sebelum dan sesudah. Mode ini sengaja memberi jeda pada operasi baca-ubah-tulis agar race condition terlihat. Lalu ulangi dengan server normal dan `--count 50 --unsafe` dilepas; lock membuat update saldo menjadi satu bagian kritis. Perbedaan hasil dapat bervariasi karena penjadwalan thread.

Untuk L3.4, jalankan server terpisah bergantian dengan konfigurasi berikut:

```powershell
python .\praktikum2_grpc\server_grpc.py --max-workers 1 --delay 0.1
python .\praktikum3_kegagalan\eksperimen.py --benchmark
```

Ulangi dengan `--max-workers 4` dan `--max-workers 10`. Catat waktu total, throughput, dan latensi rata-rata yang dicetak client ke tabel laporan. Eksperimen memakai 200 permintaan dari 20 thread. Hasil dipengaruhi CPU dan beban sistem; kenaikan worker tidak selalu menaikkan throughput tanpa batas.

| max_workers | Waktu total (s) | Throughput (req/s) | Latensi rata-rata (ms) |
|---:|---:|---:|---:|
| 1 | isi hasil ukur | isi hasil ukur | isi hasil ukur |
| 4 | isi hasil ukur | isi hasil ukur | isi hasil ukur |
| 10 | isi hasil ukur | isi hasil ukur | isi hasil ukur |

Untuk L3.5, jalankan dua server pada dua terminal:

```powershell
python .\praktikum2_grpc\server_grpc.py --port 50051
python .\praktikum2_grpc\server_grpc.py --port 50052
```

Hentikan server pertama untuk memaksa failover, lalu jalankan:

```powershell
python .\praktikum3_kegagalan\eksperimen.py --failover
```

Client mencoba endpoint kedua hanya jika menerima `UNAVAILABLE`. Kedua server contoh adalah proses terpisah dengan data memori yang berbeda; ini menunjukkan pemilihan endpoint, bukan replikasi state produksi.

## Analisis toleransi kegagalan

Cache `PROSES` berada di memori. Jika server restart, cache hilang sementara client mungkin masih retry dengan request ID lama; server baru bisa menganggapnya sebagai transaksi baru. Untuk mempertahankan semantik at-most-once melintasi restart, simpan request ID, status, dan hasil transaksi secara persisten dengan batasan unik, dan commit catatan idempotensi serta perubahan saldo dalam transaksi database yang sama. Ini memberi deduplikasi tahan restart; exactly-once end-to-end tetap memerlukan desain protokol dan efek samping yang transaksional.

