"""Generate modul Python dari kontrak akademik.proto."""

from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
subprocess.run(
    [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{HERE}",
        f"--python_out={HERE}",
        f"--grpc_python_out={HERE}",
        str(HERE / "akademik.proto"),
    ],
    check=True,
)
print("Stub berhasil dibuat: akademik_pb2.py dan akademik_pb2_grpc.py")
