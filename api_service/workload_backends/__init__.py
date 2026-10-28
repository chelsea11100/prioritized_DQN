from .base import WorkloadBackend
from .simulator_backend import SimulatorBackend
from .wrk2_backend import Wrk2Backend

__all__ = ["WorkloadBackend", "SimulatorBackend", "Wrk2Backend", "create_workload_backend"]


def create_workload_backend(backend: str, settings) -> WorkloadBackend:
    name = (backend or "simulator").lower()
    if name == "simulator":
        return SimulatorBackend(settings)
    if name in ("wrk2", "real"):
        return Wrk2Backend(settings)
    raise ValueError(f"Unknown workload backend: {backend}")
