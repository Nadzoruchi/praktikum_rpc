from pathlib import Path
from docx import Document

source = Path(r"Z:\4.College\3.Tugas\S5\Komputasi Paralel dan Terdistribusi [Pak Randi]\Laporan Praktikum 4_M Zaki Zaidan B_247006111134_E.docx")
output = Path(r"Z:\4.College\2.Koding\S5\KPT\Tugas5_RPC\Laporan Praktikum 4_M Zaki Zaidan B_247006111134_E_lengkap.docx")

doc = Document(source)
theory_anchor = next(p for p in doc.paragraphs if p.text.strip() == "Latihan Soal Teori")

intro = [
    ("Heading 1", "2. Tujuan dan Dasar Teori Singkat"),
    ("Heading 2", "Tujuan"),
    ("Normal", "Praktikum ini bertujuan memahami komunikasi prosedur jarak jauh pada sistem terdistribusi. Kegiatan mencakup pembuatan layanan XML-RPC dan gRPC, penggunaan Protocol Buffers sebagai kontrak data, serta pengamatan proses serialisasi dan pertukaran pesan antara client dan server. Praktikum juga mempelajari pemanggilan streaming, pemrosesan serentak, timeout, retry, deduplikasi permintaan, dan pengukuran kinerja layanan."),
    ("Heading 2", "Dasar Teori"),
    ("Normal", "Remote Procedure Call (RPC) memungkinkan program client memanggil prosedur pada server seolah-olah prosedur tersebut berada di program lokal. Client stub mengemas nama prosedur dan parameternya melalui proses marshalling, lalu mengirimkannya melalui jaringan. Server stub menerima dan membongkar pesan, menjalankan prosedur layanan, kemudian mengirim hasil kembali kepada client. Karena komunikasi melewati jaringan, RPC memiliki latensi lebih tinggi dan dapat mengalami kegagalan parsial, seperti server tidak tersedia atau balasan terlambat."),
    ("Normal", "XML-RPC merepresentasikan data dengan XML berbentuk teks. gRPC menggunakan Protocol Buffers untuk serialisasi biner dan HTTP/2 sebagai transport, serta mendukung pola unary dan streaming. Server gRPC dapat menangani beberapa permintaan dengan thread pool. Timeout membatasi lama client menunggu respons, sedangkan retry dapat membantu saat gangguan sementara. Namun, retry berisiko mengulang operasi yang sudah berhasil jika respons hilang. ID permintaan dan deduplikasi dapat mencegah pemrosesan ganda selama catatannya tersedia; penyimpanan di memori akan hilang ketika server restart."),
]

for style, text in intro:
    theory_anchor.insert_paragraph_before(text, style=style)

doc.add_paragraph("6. Kesimpulan dan Kendala yang Dihadapi", style="Heading 1")
doc.add_paragraph("Praktikum menunjukkan bahwa RPC memudahkan client menggunakan layanan pada server melalui antarmuka prosedur. XML-RPC memperlihatkan proses marshalling melalui pesan XML, sedangkan gRPC menggunakan Protocol Buffers dan mendukung komunikasi unary maupun streaming. Eksperimen toleransi kegagalan menunjukkan manfaat request ID untuk deduplikasi dan pentingnya lock saat beberapa thread mengubah saldo secara bersamaan. Pada pengukuran L3.4, kenaikan max_workers dari 1 menjadi 10 meningkatkan throughput dari 9,21 menjadi 94,85 request per detik, sementara waktu total turun dari 21,711 menjadi 2,109 detik dan latensi rata-rata turun dari 2067,97 menjadi 202,91 milidetik.", style="Normal")
doc.add_paragraph("Kendala yang ditemui antara lain batas integer XML-RPC: nilai yang melebihi rentang integer yang didukung ditolak saat serialisasi sebelum dikirim ke server. Saat menjalankan client dari Linux, path berkas harus menggunakan format Linux dan alamat tujuan harus memakai IP server Windows; alamat 0.0.0.0 hanya digunakan server untuk menerima koneksi, bukan sebagai alamat client. Benchmark juga perlu dijalankan tanpa mencetak trace verbose untuk setiap request agar pencetakan terminal tidak memperpanjang pengukuran. Kendala tersebut ditangani dengan penanganan OverflowError, penggunaan alamat dan path yang sesuai, serta trace terbatas pada contoh pesan yang diperlukan.", style="Normal")

doc.save(output)
print(output)
