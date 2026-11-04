"""Server XML-RPC kalkulator untuk Praktikum 1."""

from datetime import datetime
from math import sqrt
from xmlrpc.server import SimpleXMLRPCServer


def tambah(a, b):
    return a + b


def kali(a, b):
    return a * b


def bagi(a, b):
    if b == 0:
        raise ValueError("Pembagian dengan nol")
    return a / b


def pangkat(a, b):
    return a**b


def akar(x):
    if x < 0:
        raise ValueError("Akar kuadrat bilangan negatif tidak didukung")
    return sqrt(x)


def statistik(daftar):
    if not daftar:
        raise ValueError("Daftar angka tidak boleh kosong")
    return {"min": min(daftar), "max": max(daftar), "rata2": sum(daftar) / len(daftar)}


def inspeksi_datetime(value):
    """XML-RPC membawa tanggal sebagai xmlrpc.client.DateTime di sisi server."""
    return {"tipe": type(value).__name__, "nilai": value.value}


def info_server():
    return {"waktu": datetime.now().isoformat(timespec="seconds"), "status": "aktif"}


def serve(host="0.0.0.0", port=8000):
    with SimpleXMLRPCServer((host, port), allow_none=True, logRequests=True) as server:
        server.register_introspection_functions()
        for function in (tambah, kali, bagi, pangkat, akar, statistik, inspeksi_datetime, info_server):
            server.register_function(function)
        print(f"Server XML-RPC berjalan di http://{host}:{port}/ (Ctrl+C untuk berhenti)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Server XML-RPC dihentikan.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serve(args.host, args.port)
