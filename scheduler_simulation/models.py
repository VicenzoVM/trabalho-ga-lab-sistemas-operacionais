from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Pod:
    name: str
    workload: str
    cpu: float
    memory_gb: float
    disk_gb: float
    max_latency_ms: float


@dataclass
class Worker:
    name: str
    total_cpu: float
    total_memory_gb: float
    total_disk_gb: float
    network_latencies_ms: Dict[str, float]
    pods: List[Pod] = field(default_factory=list)

    @property
    def used_cpu(self) -> float:
        return sum(pod.cpu for pod in self.pods)

    @property
    def used_memory_gb(self) -> float:
        return sum(pod.memory_gb for pod in self.pods)

    @property
    def used_disk_gb(self) -> float:
        return sum(pod.disk_gb for pod in self.pods)

    @property
    def available_cpu(self) -> float:
        return self.total_cpu - self.used_cpu

    @property
    def available_memory_gb(self) -> float:
        return self.total_memory_gb - self.used_memory_gb

    @property
    def available_disk_gb(self) -> float:
        return self.total_disk_gb - self.used_disk_gb

    @property
    def average_latency_ms(self) -> float:
        latencies = [
            latency
            for worker_name, latency in self.network_latencies_ms.items()
            if worker_name != self.name
        ]
        if not latencies:
            return 0.0
        return sum(latencies) / len(latencies)

    def can_fit_all_metrics(self, pod: Pod) -> bool:
        return (
            self.available_cpu >= pod.cpu
            and self.available_memory_gb >= pod.memory_gb
            and self.available_disk_gb >= pod.disk_gb
            and self.average_latency_ms <= pod.max_latency_ms
        )

    def can_fit_kubernetes_like(self, pod: Pod) -> bool:
        # Simula a decisao padrao solicitada no enunciado: CPU e memoria apenas.
        return self.available_cpu >= pod.cpu and self.available_memory_gb >= pod.memory_gb

    def assign(self, pod: Pod) -> None:
        self.pods.append(pod)

    def cpu_utilization(self) -> float:
        return safe_ratio(self.used_cpu, self.total_cpu)

    def memory_utilization(self) -> float:
        return safe_ratio(self.used_memory_gb, self.total_memory_gb)

    def disk_utilization(self) -> float:
        return safe_ratio(self.used_disk_gb, self.total_disk_gb)

    def clone_empty(self) -> "Worker":
        return Worker(
            name=self.name,
            total_cpu=self.total_cpu,
            total_memory_gb=self.total_memory_gb,
            total_disk_gb=self.total_disk_gb,
            network_latencies_ms=dict(self.network_latencies_ms),
        )


@dataclass(frozen=True)
class SchedulingDecision:
    pod: Pod
    worker: Optional[Worker]
    score: float
    reason: str


@dataclass
class SchedulingResult:
    scheduler_name: str
    workers: List[Worker]
    decisions: List[SchedulingDecision]

    @property
    def scheduled_count(self) -> int:
        return sum(1 for decision in self.decisions if decision.worker is not None)

    @property
    def rejected_count(self) -> int:
        return sum(1 for decision in self.decisions if decision.worker is None)

    @property
    def rejected_decisions(self) -> List[SchedulingDecision]:
        return [decision for decision in self.decisions if decision.worker is None]


def safe_ratio(value: float, total: float) -> float:
    if total == 0:
        return 0.0
    return value / total
