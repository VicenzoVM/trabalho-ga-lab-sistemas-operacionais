from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from .models import Pod, Worker


@dataclass(frozen=True)
class WorkloadProfile:
    name: str
    min_cpu: float
    max_cpu: float
    min_memory_gb: float
    max_memory_gb: float
    min_disk_gb: float
    max_disk_gb: float
    min_max_latency_ms: float
    max_max_latency_ms: float


def generate_workers(count: int, seed: int) -> List[Worker]:
    rng = random.Random(seed)
    names = [f"worker-{index:02d}" for index in range(1, count + 1)]
    workers: List[Worker] = []

    for name in names:
        workers.append(
            Worker(
                name=name,
                total_cpu=float(rng.choice([24, 32, 40, 48])),
                total_memory_gb=float(rng.choice([64, 96, 128, 160])),
                total_disk_gb=float(rng.choice([300, 450, 600, 800])),
                network_latencies_ms={},
            )
        )

    # Cria uma matriz simetrica de latencia entre Workers.
    for source_index, source in enumerate(workers):
        for target_index, target in enumerate(workers):
            if source.name == target.name:
                source.network_latencies_ms[target.name] = 0.0
            elif target.name not in source.network_latencies_ms:
                distance = abs(source_index - target_index)
                latency = rng.randint(8, 35) + distance * rng.randint(12, 35)
                if rng.random() < 0.25:
                    latency += rng.randint(20, 60)
                source.network_latencies_ms[target.name] = latency
                target.network_latencies_ms[source.name] = latency

    return workers


def generate_pods(count: int, seed: int) -> List[Pod]:
    rng = random.Random(seed)
    workloads = [
        WorkloadProfile("api", 0.5, 2.0, 0.5, 4.0, 2.0, 12.0, 35.0, 75.0),
        WorkloadProfile("cache", 1.0, 3.0, 4.0, 12.0, 4.0, 24.0, 30.0, 65.0),
        WorkloadProfile("database", 2.0, 5.0, 6.0, 16.0, 35.0, 95.0, 55.0, 110.0),
        WorkloadProfile("batch", 1.0, 6.0, 2.0, 10.0, 15.0, 60.0, 90.0, 160.0),
        WorkloadProfile("analytics", 2.0, 7.0, 8.0, 20.0, 20.0, 80.0, 80.0, 145.0),
    ]
    pods: List[Pod] = []

    for index in range(1, count + 1):
        profile = rng.choice(workloads)
        pods.append(
            Pod(
                name=f"pod-{index:02d}",
                workload=profile.name,
                cpu=round(rng.uniform(profile.min_cpu, profile.max_cpu), 1),
                memory_gb=round(
                    rng.uniform(profile.min_memory_gb, profile.max_memory_gb),
                    1,
                ),
                disk_gb=round(rng.uniform(profile.min_disk_gb, profile.max_disk_gb), 1),
                max_latency_ms=round(
                    rng.uniform(
                        profile.min_max_latency_ms,
                        profile.max_max_latency_ms,
                    ),
                    1,
                ),
            )
        )

    return pods
