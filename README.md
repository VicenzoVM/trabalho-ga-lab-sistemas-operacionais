# Simulação de escalonamento de PODs

Este projeto implementa, em Python puro, uma simulação de um orquestrador
inspirado no Kubernetes. A solução não usa Kubernetes real: ela cria estruturas
de Master, Workers e PODs, executa um algoritmo de escalonamento próprio e
mostra a alocação final no terminal.

## Como executar

Não há dependências externas. Basta usar Python 3.

```bash
python3 main.py
```

Exemplo com parâmetros:

```bash
python3 main.py --workers 4 --pods 30 --seed 7
```

Parâmetros disponíveis:

| Parâmetro | Padrão | Descrição |
| --- | ---: | --- |
| `--workers` | `3` | Quantidade de nodos Workers. Mínimo: 2. |
| `--pods` | `20` | Quantidade de PODs gerados. Mínimo: 11. |
| `--seed` | `42` | Semente usada para repetir a mesma simulação. |

## Estrutura do código

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Ponto de entrada da aplicação CLI. |
| `scheduler_simulation/cli.py` | Leitura de parâmetros e montagem da simulação. |
| `scheduler_simulation/models.py` | Estruturas de POD, Worker e resultado. |
| `scheduler_simulation/master.py` | Estrutura do nodo Master. |
| `scheduler_simulation/scheduler.py` | Escalonador proposto e escalonador Kubernetes-like. |
| `scheduler_simulation/generator.py` | Geração reprodutível de Workers e PODs. |
| `scheduler_simulation/stats.py` | Cálculo de estatísticas. |
| `scheduler_simulation/reporting.py` | Saída tabular no terminal. |

## Modelo da simulação

O Master possui uma lista de Workers e um escalonador. Para cada POD criado, o
Master chama o escalonador, recebe a decisão e registra o POD no Worker escolhido.

Cada Worker possui:

- CPU total.
- Memória total.
- Disco total.
- Matriz de latências para os outros Workers.
- Lista de PODs alocados.

Cada POD possui:

- Requisito de CPU.
- Requisito de memória.
- Requisito de disco.
- Latência máxima aceitável.
- Tipo de carga, como `api`, `cache`, `database`, `batch` ou `analytics`.

## Algoritmo de escalonamento proposto

O escalonador `ResourceAwareScheduler` filtra primeiro os Workers que conseguem
receber o POD considerando todas as métricas:

1. CPU disponível maior ou igual à CPU solicitada.
2. Memória disponível maior ou igual à memória solicitada.
3. Disco disponível maior ou igual ao disco solicitado.
4. Latência média do Worker menor ou igual à latência máxima do POD.

Depois disso, calcula uma pontuação para cada Worker candidato:

```text
score = CPU_livre_após_alocação * 0.30
      + memória_livre_após_alocação * 0.25
      + disco_livre_após_alocação * 0.25
      + aderência_de_latência * 0.20
      - penalidade_de_desequilíbrio * 0.10
```

A penalidade de desequilíbrio usa o desvio padrão das utilizações de CPU,
memória e disco após a possível alocação. Isso evita escolher um Worker que
ficaria muito pressionado em apenas uma dimensão de recurso.

## Saídas apresentadas

A execução mostra:

- Capacidades iniciais dos Workers.
- Lista de PODs criados.
- Decisão tomada para cada POD.
- Estado final dos Workers, incluindo PODs alocados.
- Recursos usados, totais e livres por Worker.
- PODs não alocados e seus motivos.
- Estatísticas gerais do escalonamento.
- Comparação com o escalonador Kubernetes-like.

## Comparação com Kubernetes-like

O escalonador `KubernetesLikeScheduler` representa a regra simplificada descrita
no enunciado: ele considera apenas CPU e memória. Essa comparação permite ver
casos em que um POD seria alocado pelo critério padrão, mas produziria problemas
quando a simulação também exige disco e latência.

Na solução proposta, um POD pode ser rejeitado mesmo havendo CPU e memória
livres, caso não exista disco suficiente ou caso a latência média do Worker
ultrapasse o limite do POD. Essa decisão é mais conservadora, mas evita
alocações que violam métricas adicionais do ambiente.

## Observação

Todos os dados são simulados. A opção `--seed` permite repetir exatamente a
mesma configuração de Workers, PODs e latências para comparação e apresentação.
