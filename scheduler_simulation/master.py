from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol

from .models import Pod, SchedulingDecision, SchedulingResult, Worker


class Scheduler(Protocol):
    name: str

    def select_worker(self, pod: Pod, workers: List[Worker]) -> SchedulingDecision:
        ...


@dataclass
class Master:
    name: str
    workers: List[Worker]
    scheduler: Scheduler

    def schedule(self, pods: Iterable[Pod]) -> SchedulingResult:
        decisions: List[SchedulingDecision] = []

        for pod in pods:
            decision = self.scheduler.select_worker(pod, self.workers)
            if decision.worker is not None:
                decision.worker.assign(pod)
            decisions.append(decision)

        return SchedulingResult(
            scheduler_name=self.scheduler.name,
            workers=self.workers,
            decisions=decisions,
        )
