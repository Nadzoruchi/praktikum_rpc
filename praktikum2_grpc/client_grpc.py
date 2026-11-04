"""Demo unary, server streaming, client streaming, dan RPC asynchronous."""

import xmlrpc.client

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


def main():
    with grpc.insecure_channel("localhost:50051") as channel:
        grpc.channel_ready_future(channel).result(timeout=5)
        stub = pb_grpc.LayananNilaiStub(channel)

        print("=== Praktikum 2: gRPC dan Protocol Buffers ===")
        print("\n[Demo dasar - unary dan server streaming]")
        mahasiswa = stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"), timeout=3)
        print(f"{mahasiswa.nama} ({mahasiswa.prodi}) - IPK {mahasiswa.ipk:.2f}")

        status = stub.TambahNilai(
            pb.NilaiRequest(nim="2023001", matkul="Komputasi Paralel", nilai=88), timeout=3
        )
        print(status.pesan)

        print("Nilai (server streaming):")
        for nilai in stub.StreamNilai(pb.MahasiswaRequest(nim="2023001"), timeout=5):
            print(f"  {nilai.matkul}: {nilai.nilai}")

        print("\n[L2.1 - Client streaming: KirimBanyakNilai]")
        requests = (
            pb.NilaiRequest(nim="2023002", matkul=f"Praktikum {i}", nilai=80 + i)
            for i in range(1, 4)
        )
        print("Client streaming:", stub.KirimBanyakNilai(requests, timeout=3).pesan)

        print("\n[L2.2 - Bidirectional streaming: Diskusi]")
        # Kirim satu pesan ke ruang kelas, lalu tampilkan pesan yang diterima.
        def pesan_keluar():
            yield pb.Pesan(pengirim="Client-demo", isi="Halo ruang diskusi", ruang="kelas")

        for pesan in stub.Diskusi(pesan_keluar(), timeout=2):
            print(f"  [{pesan.ruang}] {pesan.pengirim}: {pesan.isi}")
            break

        print("\n[L2.3 - Field baru dan backward compatibility]")
        print(f"Mahasiswa dari server baru: prodi={mahasiswa.prodi!r}")
        print("Catatan: uji client lama perlu dijalankan dengan stub versi lama yang belum digenerate ulang.")

        print("\n[L2.4 - Perbandingan ukuran pesan]")
        encoded = mahasiswa.SerializeToString()
        print(f"Ukuran Mahasiswa Protobuf: {len(encoded)} byte")
        xml_message = xmlrpc.client.dumps(
            ({"nim": mahasiswa.nim, "nama": mahasiswa.nama,
              "ipk": mahasiswa.ipk, "prodi": mahasiswa.prodi},),
            methodname="GetMahasiswa",
        ).encode("utf-8")
        print(f"Ukuran XML-RPC untuk field yang sama: {len(xml_message)} byte")
        print("Perbandingan ini mengukur body serialisasi, tidak termasuk header HTTP/2/HTTP.")

        print("\n[L2.5 - Sepuluh pemanggilan asynchronous]")
        # future() mengirim permintaan tanpa menunggu hasil tiap panggilan.
        calls = [
            stub.GetMahasiswa.future(pb.MahasiswaRequest(nim="2023001"), timeout=3)
            for _ in range(10)
        ]
        print("Hasil 10 future:", [call.result().nama for call in calls])

        try:
            stub.GetMahasiswa(pb.MahasiswaRequest(nim="9999"), timeout=3)
        except grpc.RpcError as error:
            print(f"NIM tidak ditemukan: {error.code().name}: {error.details()}")

if __name__ == "__main__":
    main()
