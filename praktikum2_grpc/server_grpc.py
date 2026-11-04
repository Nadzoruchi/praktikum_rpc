"""Server gRPC untuk Praktikum 2 dan 3. Jalankan generate_stubs.py dahulu."""

import argparse
import queue
import random
import threading
import time
from concurrent import futures

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


DATA = {
    "2023001": {"nama": "Andi", "prodi": "Informatika", "nilai": {"Basis Data": 85.0, "Jaringan": 78.0}},
    "2023002": {"nama": "Sari", "prodi": "Sistem Informasi", "nilai": {"Basis Data": 92.0}},
}
SALDO = {"A": 1000.0, "B": 500.0}
PROSES = {}  # request_id -> hasil; hanya bertahan selama proses server hidup
LOCK = threading.Lock()


class ChatHub:
    """Relay pesan sederhana ke semua client yang berlangganan dalam satu ruang."""

    def __init__(self):
        self.lock = threading.Lock()
        self.subscribers = {}

    def subscribe(self, room):
        inbox = queue.Queue()
        with self.lock:
            self.subscribers.setdefault(room, set()).add(inbox)
        return inbox

    def unsubscribe(self, room, inbox):
        with self.lock:
            members = self.subscribers.get(room, set())
            members.discard(inbox)
            if not members:
                self.subscribers.pop(room, None)

    def publish(self, room, message):
        with self.lock:
            recipients = tuple(self.subscribers.get(room, ()))
        for inbox in recipients:
            inbox.put(message)


CHAT = ChatHub()


class LayananNilai(pb_grpc.LayananNilaiServicer):
    def __init__(self, delay=0.0, unsafe_transfer=False, slow_transfer=False):
        self.delay = delay
        self.unsafe_transfer = unsafe_transfer
        self.slow_transfer = slow_transfer

    def GetMahasiswa(self, request, context):
        if self.delay:
            time.sleep(self.delay)
        mhs = DATA.get(request.nim)
        if mhs is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"NIM {request.nim} tidak ditemukan")
        grades = list(mhs["nilai"].values())
        ipk = sum(grades) / len(grades) / 25 if grades else 0.0
        return pb.Mahasiswa(nim=request.nim, nama=mhs["nama"], prodi=mhs["prodi"], ipk=round(ipk, 2))

    def TambahNilai(self, request, context):
        if not request.nim or not request.matkul:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "NIM dan nama mata kuliah wajib diisi")
        if not 0 <= request.nilai <= 100:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Nilai harus 0-100")
        with LOCK:
            mhs = DATA.setdefault(request.nim, {"nama": "(baru)", "prodi": "Belum diisi", "nilai": {}})
            mhs["nilai"][request.matkul] = request.nilai
        return pb.StatusResponse(sukses=True, pesan="Nilai tersimpan")

    def StreamNilai(self, request, context):
        mhs = DATA.get(request.nim)
        if mhs is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "NIM tidak ditemukan")
        for matkul, nilai in tuple(mhs["nilai"].items()):
            if not context.is_active():
                return
            yield pb.Nilai(matkul=matkul, nilai=nilai)
            time.sleep(0.5)

    def KirimBanyakNilai(self, request_iterator, context):
        tersimpan = 0
        for request in request_iterator:
            if not request.nim or not request.matkul or not 0 <= request.nilai <= 100:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Setiap nilai harus memiliki NIM, matkul, dan nilai 0-100")
            with LOCK:
                mhs = DATA.setdefault(request.nim, {"nama": "(baru)", "prodi": "Belum diisi", "nilai": {}})
                mhs["nilai"][request.matkul] = request.nilai
            tersimpan += 1
        return pb.StatusResponse(sukses=True, pesan=f"{tersimpan} nilai tersimpan")

    def Diskusi(self, request_iterator, context):
        first = None
        try:
            first = next(request_iterator)
        except StopIteration:
            return
        room = first.ruang or "umum"
        inbox = CHAT.subscribe(room)

        def baca_dan_sebarkan():
            try:
                CHAT.publish(room, first)
                for pesan in request_iterator:
                    CHAT.publish(room, pesan)
            except grpc.RpcError:
                # Client membatalkan stream atau memutus koneksi.
                return

        reader = threading.Thread(target=baca_dan_sebarkan, daemon=True)
        reader.start()
        try:
            while context.is_active():
                try:
                    yield inbox.get(timeout=0.2)
                except queue.Empty:
                    if not reader.is_alive():
                        break
        finally:
            CHAT.unsubscribe(room, inbox)

    def Transfer(self, request, context):
        if request.jumlah <= 0 or request.dari not in SALDO or request.ke not in SALDO or request.dari == request.ke:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Akun atau jumlah transfer tidak valid")
        if not request.request_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "request_id wajib diisi untuk deduplikasi")

        def apply_transfer():
            if request.request_id in PROSES:
                return PROSES[request.request_id]
            if SALDO[request.dari] < request.jumlah:
                result = pb.StatusResponse(sukses=False, pesan="Saldo tidak cukup")
            else:
                SALDO[request.dari] -= request.jumlah
                SALDO[request.ke] += request.jumlah
                result = pb.StatusResponse(sukses=True, pesan=f"Saldo kini {dict(SALDO)}")
            PROSES[request.request_id] = result
            return result

        if self.unsafe_transfer:
            # Jeda membuka jendela race agar kehilangan update bisa diamati pada eksperimen.
            result = PROSES.get(request.request_id)
            if result is None:
                available = SALDO[request.dari] >= request.jumlah
                time.sleep(0.002)
                if available:
                    saldo_dari_baru = SALDO[request.dari] - request.jumlah
                    saldo_ke_baru = SALDO[request.ke] + request.jumlah
                    time.sleep(0.002)  # memperbesar peluang dua thread menulis snapshot yang sama
                    SALDO[request.dari] = saldo_dari_baru
                    SALDO[request.ke] = saldo_ke_baru
                    result = pb.StatusResponse(sukses=True, pesan="Transfer selesai (mode tanpa lock)")
                else:
                    result = pb.StatusResponse(sukses=False, pesan="Saldo tidak cukup")
                PROSES[request.request_id] = result
        else:
            with LOCK:
                result = apply_transfer()

        # Saldo/hasil sudah dicatat sebelum sleep, sehingga deadline dapat terjadi sesudah commit.
        if self.slow_transfer and random.random() < 0.3:
            time.sleep(3)
        return result

    def GetSaldo(self, request, context):
        with LOCK:
            saldo_a = SALDO["A"]
            saldo_b = SALDO["B"]
        return pb.SaldoResponse(saldo_a=saldo_a, saldo_b=saldo_b, total=saldo_a + saldo_b)


def serve(host="[::]", port=50051, max_workers=10, delay=0.0, unsafe_transfer=False, slow_transfer=False):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    pb_grpc.add_LayananNilaiServicer_to_server(
        LayananNilai(delay=delay, unsafe_transfer=unsafe_transfer, slow_transfer=slow_transfer), server
    )
    bound_port = server.add_insecure_port(f"{host}:{port}")
    if not bound_port:
        raise RuntimeError(f"Gagal membuka port {host}:{port}")
    server.start()
    print(f"Server gRPC berjalan di {host}:{port}, max_workers={max_workers}, delay={delay}s")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=2).wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="[::]")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--max-workers", type=int, default=10)
    parser.add_argument("--delay", type=float, default=0.0, help="delay GetMahasiswa untuk uji throughput")
    parser.add_argument("--unsafe-transfer", action="store_true", help="hilangkan lock untuk L3.3")
    parser.add_argument("--slow-transfer", action="store_true", help="peluang 30%% balasan terlambat untuk uji retry")
    args = parser.parse_args()
    serve(args.host, args.port, args.max_workers, args.delay, args.unsafe_transfer, args.slow_transfer)
