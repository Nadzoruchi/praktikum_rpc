"""Eksperimen retry, deduplikasi, race condition, throughput, dan failover."""

import argparse
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "praktikum2_grpc"))

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


def open_stub(address):
    channel = grpc.insecure_channel(address)
    return channel, pb_grpc.LayananNilaiStub(channel)


def run_transfers(address, count, unsafe, same_id):
    channel, stub = open_stub(address)
    try:
        def one(_index):
            request_id = str(uuid.uuid4())
            for attempt in range(1, 4):
                rid = request_id if same_id else str(uuid.uuid4())
                req = pb.TransferRequest(request_id=rid, dari="A", ke="B", jumlah=10)
                try:
                    return stub.Transfer(req, timeout=2)
                except grpc.RpcError as error:
                    if error.code() not in (grpc.StatusCode.DEADLINE_EXCEEDED, grpc.StatusCode.UNAVAILABLE) or attempt == 3:
                        return None
                    time.sleep(0.5 * 2 ** (attempt - 1))

        with ThreadPoolExecutor(max_workers=10 if unsafe else 4) as pool:
            results = list(pool.map(one, range(count)))
        print(f"Permintaan={count}, respons gagal/timeout akhir={sum(r is None for r in results)}")
        saldo = stub.GetSaldo(pb.Empty(), timeout=3)
        print(f"Saldo akhir: A={saldo.saldo_a:.2f}, B={saldo.saldo_b:.2f}, total={saldo.total:.2f}")
        if unsafe:
            print("Mode tanpa lock aktif. Bandingkan total saldo A+B dengan 1500.0.")
        elif same_id:
            print("ID tetap per operasi: retry tidak mengulangi efek transfer yang sudah dicatat.")
        else:
            print("ID baru per retry: deadline setelah commit dapat menyebabkan transfer ganda.")
    finally:
        channel.close()


def benchmark(address, requests=200, concurrency=20):
    channel, stub = open_stub(address)
    try:
        def call(_):
            start = time.perf_counter()
            stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"), timeout=10)
            return time.perf_counter() - start

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            latencies = list(pool.map(call, range(requests)))
        elapsed = time.perf_counter() - start
        throughput = requests / elapsed
        average_ms = sum(latencies) / len(latencies) * 1000
        print(f"max_workers server (atur saat start): throughput={throughput:.2f} req/s, "
              f"waktu={elapsed:.3f}s, latensi rata-rata={average_ms:.2f}ms")
        return elapsed, throughput, average_ms
    finally:
        channel.close()


def benchmark_all(address, requests=200, concurrency=20):
    print("Mulai server dengan --max-workers masing-masing 1, 4, dan 10 serta --delay 0.1.")
    benchmark(address, requests, concurrency)


def failover(addresses, nim="2023001"):
    last_error = None
    for address in addresses:
        channel, stub = open_stub(address)
        try:
            response = stub.GetMahasiswa(pb.MahasiswaRequest(nim=nim), timeout=3)
            print(f"Berhasil melalui {address}: {response.nama}, IPK {response.ipk:.2f}")
            return response
        except grpc.RpcError as error:
            last_error = error
            if error.code() != grpc.StatusCode.UNAVAILABLE:
                raise
            print(f"{address} UNAVAILABLE; mencoba endpoint berikutnya")
        finally:
            channel.close()
    raise RuntimeError("Semua endpoint gagal") from last_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default="localhost:50051")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--unsafe", action="store_true", help="jalankan L3.3 (server harus --unsafe-transfer)")
    parser.add_argument("--new-id-per-retry", action="store_true", help="jalankan L3.2")
    parser.add_argument("--benchmark", action="store_true", help="jalankan benchmark 200 request/20 thread")
    parser.add_argument("--failover", action="store_true", help="coba localhost:50051 lalu localhost:50052")
    args = parser.parse_args()

    if args.failover:
        failover(["localhost:50051", "localhost:50052"])
    elif args.benchmark:
        benchmark(args.address)
    else:
        run_transfers(args.address, args.count, args.unsafe, not args.new_id_per_retry)


if __name__ == "__main__":
    main()
