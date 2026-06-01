from __future__ import annotations

import argparse

from .generator import generate_pods, generate_workers
from .master import Master
from .reporting import print_full_report
from .scheduler import KubernetesLikeScheduler, ResourceAwareScheduler, clone_workers


def main() -> None:
    args = parse_args()
    validate_args(args)

    workers = generate_workers(args.workers, args.seed)
    pods = generate_pods(args.pods, args.seed + 1000)

    proposed_workers = clone_workers(workers)
    kubernetes_workers = clone_workers(workers)

    proposed_master = Master(
        name="master-01",
        workers=proposed_workers,
        scheduler=ResourceAwareScheduler(),
    )
    kubernetes_master = Master(
        name="master-01",
        workers=kubernetes_workers,
        scheduler=KubernetesLikeScheduler(),
    )

    proposed_result = proposed_master.schedule(pods)
    kubernetes_result = kubernetes_master.schedule(pods)

    print_full_report(
        master_name=proposed_master.name,
        workers_before=workers,
        pods=pods,
        proposed_result=proposed_result,
        kubernetes_result=kubernetes_result,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Simulacao de escalonamento de PODs com um Master e varios Workers."
        )
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="quantidade de nodos Workers (minimo: 2, padrao: 3)",
    )
    parser.add_argument(
        "--pods",
        type=int,
        default=20,
        help="quantidade de PODs gerados (minimo: 11, padrao: 20)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="semente para tornar a simulacao reprodutivel (padrao: 42)",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.workers < 2:
        raise SystemExit("Erro: use ao menos 2 Workers.")
    if args.pods < 11:
        raise SystemExit("Erro: use ao menos 11 PODs para cumprir o enunciado.")
