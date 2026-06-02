from __future__ import annotations

from typing import Iterable, List, Sequence

from .models import Pod, SchedulingResult, Worker
from .stats import ResultStats, calculate_stats


def print_full_report(
    master_name: str,
    workers_before: List[Worker],
    pods: List[Pod],
    proposed_result: SchedulingResult,
    kubernetes_result: SchedulingResult,
) -> None:
    print_title("Simulacao de escalonamento de PODs")
    print(f"Master: {master_name}")
    print(f"Workers: {len(workers_before)}")
    print(f"PODs gerados: {len(pods)}")
    print()

    print_workers_capacity(workers_before)
    print_pod_requirements(pods)
    print_schedule_result(proposed_result)
    print_stats(proposed_result)
    print_comparison(proposed_result, kubernetes_result)


def print_workers_capacity(workers: List[Worker]) -> None:
    print_title("Capacidade inicial dos Workers")
    rows = [
        [
            worker.name,
            format_number(worker.total_cpu),
            format_gb(worker.total_memory_gb),
            format_gb(worker.total_disk_gb),
            format_ms(worker.average_latency_ms),
        ]
        for worker in workers
    ]
    print_table(["Worker", "CPU", "Memoria", "Disco", "Latencia media"], rows)
    print()


def print_pod_requirements(pods: List[Pod]) -> None:
    print_title("PODs criados")
    rows = [
        [
            pod.name,
            pod.workload,
            format_number(pod.cpu),
            format_gb(pod.memory_gb),
            format_gb(pod.disk_gb),
            format_ms(pod.max_latency_ms),
        ]
        for pod in pods
    ]
    print_table(["POD", "Tipo", "CPU", "Memoria", "Disco", "Latencia max"], rows)
    print()


def print_schedule_result(result: SchedulingResult) -> None:
    print_title("Decisoes do escalonador proposto")
    decision_rows = []
    for decision in result.decisions:
        decision_rows.append(
            [
                decision.pod.name,
                decision.worker.name if decision.worker is not None else "-",
                f"{decision.score:.3f}",
                decision.reason,
            ]
        )
    print_table(["POD", "Worker", "Score", "Motivo"], decision_rows)
    print()

    print_title("Estado final dos Workers")
    worker_rows = []
    for worker in result.workers:
        pod_names = ", ".join(pod.name for pod in worker.pods) or "-"
        worker_rows.append(
            [
                worker.name,
                pod_names,
                resource_state(worker.used_cpu, worker.total_cpu, worker.available_cpu),
                resource_state(
                    worker.used_memory_gb,
                    worker.total_memory_gb,
                    worker.available_memory_gb,
                ),
                resource_state(
                    worker.used_disk_gb,
                    worker.total_disk_gb,
                    worker.available_disk_gb,
                ),
                format_ms(worker.average_latency_ms),
            ]
        )
    print_table(
        ["Worker", "PODs alocados", "CPU usado/total/livre", "Mem usado/total/livre", "Disco usado/total/livre", "Latencia media"],
        worker_rows,
    )
    print()

    if result.rejected_decisions:
        print_title("PODs nao alocados")
        rows = [[decision.pod.name, decision.reason] for decision in result.rejected_decisions]
        print_table(["POD", "Motivo"], rows)
        print()


def print_stats(result: SchedulingResult) -> None:
    stats = calculate_stats(result)
    print_title("Estatisticas do escalonamento proposto")
    rows = [
        ["PODs alocados", str(stats.scheduled_count)],
        ["PODs rejeitados", str(stats.rejected_count)],
        ["Uso medio de CPU", format_percent(stats.average_cpu_utilization)],
        ["Uso medio de memoria", format_percent(stats.average_memory_utilization)],
        ["Uso medio de disco", format_percent(stats.average_disk_utilization)],
        ["Workers com disco excedido", str(stats.disk_overcommit_workers)],
        ["Violacoes de latencia", str(stats.latency_violations)],
        ["Worker mais carregado", stats.most_loaded_worker],
        ["Worker menos carregado", stats.least_loaded_worker],
    ]
    print_table(["Metrica", "Valor"], rows)
    print()


def print_comparison(
    proposed_result: SchedulingResult,
    kubernetes_result: SchedulingResult,
) -> None:
    proposed_stats = calculate_stats(proposed_result)
    kubernetes_stats = calculate_stats(kubernetes_result)

    print_title("Comparacao tecnica com escalonador Kubernetes-like")
    rows = [
        [
            "Metricas consideradas",
            "CPU, memoria, disco, latencia",
            "CPU, memoria",
        ],
        [
            "PODs alocados",
            str(proposed_stats.scheduled_count),
            str(kubernetes_stats.scheduled_count),
        ],
        [
            "PODs rejeitados",
            str(proposed_stats.rejected_count),
            str(kubernetes_stats.rejected_count),
        ],
        [
            "Uso medio de CPU",
            format_percent(proposed_stats.average_cpu_utilization),
            format_percent(kubernetes_stats.average_cpu_utilization),
        ],
        [
            "Uso medio de memoria",
            format_percent(proposed_stats.average_memory_utilization),
            format_percent(kubernetes_stats.average_memory_utilization),
        ],
        [
            "Uso medio de disco",
            format_percent(proposed_stats.average_disk_utilization),
            format_percent(kubernetes_stats.average_disk_utilization),
        ],
        [
            "Workers com disco excedido",
            str(proposed_stats.disk_overcommit_workers),
            str(kubernetes_stats.disk_overcommit_workers),
        ],
        [
            "Violacoes de latencia",
            str(proposed_stats.latency_violations),
            str(kubernetes_stats.latency_violations),
        ],
    ]
    print_table(["Criterio", "Solucao proposta", "Kubernetes-like"], rows)
    print()
    


def print_title(title: str) -> None:
    print(title)
    print("=" * len(title))


def print_table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> None:
    row_list = [[str(cell) for cell in row] for row in rows]
    header_list = [str(header) for header in headers]
    widths = [
        max(len(header_list[index]), *(len(row[index]) for row in row_list))
        if row_list
        else len(header_list[index])
        for index in range(len(header_list))
    ]

    print(format_row(header_list, widths))
    print(format_row(["-" * width for width in widths], widths))
    for row in row_list:
        print(format_row(row, widths))


def format_row(row: Sequence[str], widths: Sequence[int]) -> str:
    return " | ".join(str(cell).ljust(widths[index]) for index, cell in enumerate(row))


def resource_state(used: float, total: float, available: float) -> str:
    return f"{format_number(used)}/{format_number(total)}/{format_number(available)}"


def format_gb(value: float) -> str:
    return f"{format_number(value)} GB"


def format_ms(value: float) -> str:
    return f"{format_number(value)} ms"


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"
