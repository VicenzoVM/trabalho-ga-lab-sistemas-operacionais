from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev
from typing import Dict, List, Optional, Tuple

from .models import Pod, SchedulingDecision, Worker, safe_ratio


@dataclass(frozen=True)
class ResourceAwareScheduler:
    name: str = "resource-aware"
    cpu_weight: float = 0.30
    memory_weight: float = 0.25
    disk_weight: float = 0.25
    latency_weight: float = 0.20
    balance_penalty_weight: float = 0.10

    def select_worker(self, pod: Pod, workers: List[Worker]) -> SchedulingDecision:
        best_worker: Optional[Worker] = None
        best_score = -1.0
        rejection_reasons: Dict[str, int] = {}

        for worker in workers:
            can_fit, reason = self._can_fit_with_reason(worker, pod)
            if not can_fit:
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                continue

            score = self._score(worker, pod)
            if score > best_score:
                best_score = score
                best_worker = worker

        if best_worker is None:
            reason = self._summarize_rejections(rejection_reasons)
            return SchedulingDecision(pod=pod, worker=None, score=0.0, reason=reason)

        return SchedulingDecision(
            pod=pod,
            worker=best_worker,
            score=best_score,
            reason="maior pontuacao considerando CPU, memoria, disco e latencia",
        )

    def _can_fit_with_reason(self, worker: Worker, pod: Pod) -> Tuple[bool, str]:
        if worker.available_cpu < pod.cpu:
            return False, "CPU insuficiente"
        if worker.available_memory_gb < pod.memory_gb:
            return False, "memoria insuficiente"
        if worker.available_disk_gb < pod.disk_gb:
            return False, "disco insuficiente"
        if worker.average_latency_ms > pod.max_latency_ms:
            return False, "latencia acima do limite do POD"
        return True, "ok"

    def _score(self, worker: Worker, pod: Pod) -> float:
        # Avalia como o Worker ficaria apos receber o POD.
        cpu_remaining = safe_ratio(worker.available_cpu - pod.cpu, worker.total_cpu)
        memory_remaining = safe_ratio(
            worker.available_memory_gb - pod.memory_gb,
            worker.total_memory_gb,
        )
        disk_remaining = safe_ratio(
            worker.available_disk_gb - pod.disk_gb,
            worker.total_disk_gb,
        )
        latency_score = 1.0 - safe_ratio(worker.average_latency_ms, pod.max_latency_ms)
        latency_score = clamp(latency_score, 0.0, 1.0)

        base_score = (
            cpu_remaining * self.cpu_weight
            + memory_remaining * self.memory_weight
            + disk_remaining * self.disk_weight
            + latency_score * self.latency_weight
        )

        utilizations_after = [
            1.0 - cpu_remaining,
            1.0 - memory_remaining,
            1.0 - disk_remaining,
        ]
        balance_penalty = pstdev(utilizations_after) * self.balance_penalty_weight

        return clamp(base_score - balance_penalty, 0.0, 1.0)

    def _summarize_rejections(self, rejection_reasons: Dict[str, int]) -> str:
        if not rejection_reasons:
            return "sem Workers disponiveis"
        ordered = sorted(
            rejection_reasons.items(),
            key=lambda item: (-item[1], item[0]),
        )
        return ", ".join(f"{reason}: {count}" for reason, count in ordered)


@dataclass(frozen=True)
class KubernetesLikeScheduler:
    name: str = "kubernetes-like"

    def select_worker(self, pod: Pod, workers: List[Worker]) -> SchedulingDecision:
        best_worker: Optional[Worker] = None
        best_score = -1.0

        for worker in workers:
            if not worker.can_fit_kubernetes_like(pod):
                continue

            score = self._score(worker, pod)
            if score > best_score:
                best_score = score
                best_worker = worker

        if best_worker is None:
            return SchedulingDecision(
                pod=pod,
                worker=None,
                score=0.0,
                reason="CPU ou memoria insuficiente",
            )

        return SchedulingDecision(
            pod=pod,
            worker=best_worker,
            score=best_score,
            reason="maior pontuacao considerando CPU e memoria",
        )

    def _score(self, worker: Worker, pod: Pod) -> float:
        cpu_remaining = safe_ratio(worker.available_cpu - pod.cpu, worker.total_cpu)
        memory_remaining = safe_ratio(
            worker.available_memory_gb - pod.memory_gb,
            worker.total_memory_gb,
        )
        return clamp((cpu_remaining + memory_remaining) / 2.0, 0.0, 1.0)


def clone_workers(workers: List[Worker]) -> List[Worker]:
    return [worker.clone_empty() for worker in workers]


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
