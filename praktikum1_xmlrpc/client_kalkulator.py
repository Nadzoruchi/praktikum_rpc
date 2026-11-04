"""Client dan demonstrasi seluruh latihan XML-RPC."""

import argparse
import time
import xmlrpc.client
from datetime import datetime


def benchmark(url, jumlah=100):
    # Tetap melakukan 100 RPC sungguhan, tetapi tanpa mencetak ratusan baris
    # trace ke terminal. Verbose dipakai terpisah untuk contoh L1.2.
    with xmlrpc.client.ServerProxy(url, verbose=False, allow_none=True) as proxy:
        mulai = time.perf_counter()
        for _ in range(jumlah):
            proxy.tambah(5, 3)
        waktu_rpc = time.perf_counter() - mulai

    def tambah_lokal(a, b):
        return a + b

    mulai = time.perf_counter()
    for _ in range(jumlah):
        tambah_lokal(5, 3)
    waktu_lokal = time.perf_counter() - mulai
    print(f"Benchmark {jumlah} panggilan: RPC={waktu_rpc:.6f}s, lokal={waktu_lokal:.6f}s")
    print(f"Rasio latensi total RPC/lokal: {waktu_rpc / max(waktu_lokal, 1e-12):.1f}x")


def tampilkan_ukuran_xml():
    request = xmlrpc.client.dumps((5, 3), methodname="tambah", allow_none=True)
    encoded = request.encode("utf-8")
    # Definisi transparan untuk analisis overhead: payload = dua angka ("5" dan "3").
    payload_bytes = len("5".encode()) + len("3".encode())
    print(f"Ukuran body methodCall tambah(5, 3): {len(encoded)} byte")
    print(f"Payload angka: {payload_bytes} byte ({payload_bytes / len(encoded) * 100:.1f}%)")
    print(f"Overhead XML-RPC: {len(encoded) - payload_bytes} byte ({(1-payload_bytes/len(encoded))*100:.1f}%)")
    print("XML request:\n" + request)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000/")
    parser.add_argument("--benchmark", action="store_true", help="ukur 100 RPC dan pemanggilan lokal")
    parser.add_argument("--xml-size", action="store_true", help="ukur ukuran XML methodCall")
    args = parser.parse_args()

    try:
        with xmlrpc.client.ServerProxy(args.url, allow_none=True) as proxy:
            print("=== Demo XML-RPC ===")
            print("\n[L1.1 - Pangkat dan akar]")
            print(f"5 + 3       = {proxy.tambah(5, 3)}")
            print(f"4 x 7       = {proxy.kali(4, 7)}")
            print(f"2 pangkat 8 = {proxy.pangkat(2, 8)}")
            print(f"akar(81)    = {proxy.akar(81)}")

            print("\n[L1.2 - List dan dictionary]")
            # Trace satu request saja agar marshalling list dan dictionary terlihat.
            with xmlrpc.client.ServerProxy(args.url, verbose=True, allow_none=True) as trace_proxy:
                hasil_statistik = trace_proxy.statistik([2, 4, 6, 8])
            print("hasil statistik =", hasil_statistik)

            print("\n[L1.3 - Datetime dan integer besar]")
            try:
                print("Bilangan besar:", proxy.tambah(2**40, 1))
            except OverflowError as error:
                # XML-RPC standar hanya punya integer 32-bit; serializer menolak
                # nilainya sebelum request dikirim ke server.
                print(f"Integer > 2^31 ditolak saat serialisasi ({error}).")
                print("Request tidak sampai ke server; ini batas integer XML-RPC.")
            print("Datetime:", proxy.inspeksi_datetime(datetime(2026, 1, 2, 12, 34, 56)))
            try:
                proxy.bagi(10, 0)
            except xmlrpc.client.Fault as error:
                print(f"Pembagian nol ditangani: Fault {error.faultCode} - {error.faultString}")

            if args.benchmark:
                print("\n[L1.4 - Benchmark 100 panggilan]")
                benchmark(args.url)

            if args.xml_size:
                print("\n[Analisis ukuran pesan]")
                tampilkan_ukuran_xml()

            print("\n[L1.5 - Penanganan server mati]")
            print("Uji dengan menghentikan server lalu menjalankan client; kegagalan koneksi ditangani di bawah.")
    except (ConnectionError, OSError, xmlrpc.client.ProtocolError) as error:
        print(f"Tidak dapat menghubungi server XML-RPC di {args.url}: {error}")
        print("Pastikan server aktif dan alamat/port dapat dijangkau.")
    except xmlrpc.client.Fault as error:
        print(f"Kesalahan RPC: {error.faultString}")


if __name__ == "__main__":
    main()
