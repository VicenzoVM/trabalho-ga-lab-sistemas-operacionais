from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import SchedulingResult, Worker


@dataclass(frozen=True)
class ResultStats:
    scheduled_count: int
    rejected_count: int
    average_cpu_utilization: float
    average_memory_utilization: float
    average_disk_utilization: float
    disk_overcommit_workers: int
    latency_violations: int
    most_loaded_worker: str
    least_loaded_worker: str


def calculate_stats(result: SchedulingResult) -> ResultStats:
    workers = result.workers
    avg_cpu = average([worker.cpu_utilization() for worker in workers])
    avg_memory = average([worker.memory_utilization() for worker in workers])
    avg_disk = average([worker.disk_utilization() for worker in workers])
    disk_overcommit = sum(1 for worker in workers if worker.available_disk_gb < 0)
    latency_violations = count_latency_violations(workers)

    return ResultStats(
        scheduled_count=result.scheduled_count,
        rejected_count=result.rejected_count,
        average_cpu_utilization=avg_cpu,
        average_memory_utilization=avg_memory,
        average_disk_utilization=avg_disk,
        disk_overcommit_workers=disk_overcommit,
        latency_violations=latency_violations,
        most_loaded_worker=worker_with_highest_average_utilization(workers),
        least_loaded_worker=worker_with_lowest_average_utilization(workers),
    )


def count_latency_violations(workers: List[Worker]) -> int:
    violations = 0
    for worker in workers:
        for pod in worker.pods:
            if worker.average_latency_ms > pod.max_latency_ms:
                violations += 1
    return violations


def worker_with_highest_average_utilization(workers: List[Worker]) -> str:
    if not workers:
        return "-"
    return max(workers, key=average_worker_utilization).name


def worker_with_lowest_average_utilization(workers: List[Worker]) -> str:
    if not workers:
        return "-"
    return min(workers, key=average_worker_utilization).name


def average_worker_utilization(worker: Worker) -> float:
    return (
        worker.cpu_utilization()
        + worker.memory_utilization()
        + worker.disk_utilization()
    ) / 3.0


def average(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
