import subprocess

import torch

_limited_devices: set[tuple[int, float]] = set()


def _free_memory_mib() -> dict[int, int]:
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return {}

    free_memory: dict[int, int] = {}
    for line in completed.stdout.strip().splitlines():
        index, free = (part.strip() for part in line.split(","))
        free_memory[int(index)] = int(free)
    return free_memory


def resolve_device(preference: str) -> torch.device:
    preference = preference.strip().lower()
    if preference == "cpu":
        return torch.device("cpu")
    if not torch.cuda.is_available():
        return torch.device("cpu")
    if preference.startswith("cuda:"):
        return torch.device(preference)
    if preference == "cuda":
        return torch.device("cuda:0")

    free_memory = _free_memory_mib()
    if not free_memory:
        return torch.device("cuda:0")
    return torch.device(f"cuda:{max(free_memory, key=free_memory.get)}")


def limit_gpu_memory(device: torch.device, fraction: float) -> None:
    if device.type != "cuda" or fraction >= 1.0:
        return

    index = device.index if device.index is not None else 0
    key = (index, fraction)
    if key in _limited_devices:
        return

    torch.cuda.set_per_process_memory_fraction(fraction, index)
    _limited_devices.add(key)
