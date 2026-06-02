# Simulacao de escalonamento de PODs

Este projeto implementa, em Python puro, uma simulacao de um orquestrador
inspirado no Kubernetes. A solucao nao usa Kubernetes real: ela cria estruturas
de Master, Workers e PODs, executa um algoritmo de escalonamento proprio e
mostra a alocacao final no terminal.

## Como executar

Nao ha dependencias externas. Basta usar Python 3.

```bash
python3 main.py
```

Exemplo com parametros:

```bash
python3 main.py --workers 4 --pods 30 --seed 7
```

Parametros disponiveis:

| Parametro | Padrao | Descricao |
| --- | ---: | --- |
| `--workers` | `3` | Quantidade de nodos Workers. Minimo: 2. |
| `--pods` | `20` | Quantidade de PODs gerados. Minimo: 11. |
| `--seed` | `42` | Semente usada para repetir a mesma simulacao. |

## Estrutura do codigo

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Ponto de entrada da aplicacao CLI. |
| `scheduler_simulation/cli.py` | Leitura de parametros e montagem da simulacao. |
| `scheduler_simulation/models.py` | Estruturas de POD, Worker e resultado. |
| `scheduler_simulation/master.py` | Estrutura do nodo Master. |
| `scheduler_simulation/scheduler.py` | Escalonador proposto e escalonador Kubernetes-like. |
| `scheduler_simulation/generator.py` | Geracao reprodutivel de Workers e PODs. |
| `scheduler_simulation/stats.py` | Calculo de estatisticas. |
| `scheduler_simulation/reporting.py` | Saida tabular no terminal. |

## Modelo da simulacao

O Master possui uma lista de Workers e um escalonador. Para cada POD criado, o
Master chama o escalonador, recebe a decisao e registra o POD no Worker escolhido.

Cada Worker possui:

- CPU total.
- Memoria total.
- Disco total.
- Matriz de latencias para os outros Workers.
- Lista de PODs alocados.

Cada POD possui:

- Requisito de CPU.
- Requisito de memoria.
- Requisito de disco.
- Latencia maxima aceitavel.
- Tipo de carga, como `api`, `cache`, `database`, `batch` ou `analytics`.

## Algoritmo de escalonamento proposto

O escalonador `ResourceAwareScheduler` filtra primeiro os Workers que conseguem
receber o POD considerando todas as metricas:

1. CPU disponivel maior ou igual a CPU solicitada.
2. Memoria disponivel maior ou igual a memoria solicitada.
3. Disco disponivel maior ou igual ao disco solicitado.
4. Latencia media do Worker menor ou igual a latencia maxima do POD.

Depois disso, calcula uma pontuacao para cada Worker candidato:

```text
score = CPU_livre_apos_alocacao * 0.30
      + memoria_livre_apos_alocacao * 0.25
      + disco_livre_apos_alocacao * 0.25
      + aderencia_de_latencia * 0.20
      - penalidade_de_desequilibrio * 0.10
```

A penalidade de desequilibrio usa o desvio padrao das utilizacoes de CPU,
memoria e disco apos a possivel alocacao. Isso evita escolher um Worker que
ficaria muito pressionado em apenas uma dimensao de recurso.

## Saidas apresentadas

A execucao mostra:

- Capacidades iniciais dos Workers.
- Lista de PODs criados.
- Decisao tomada para cada POD.
- Estado final dos Workers, incluindo PODs alocados.
- Recursos usados, totais e livres por Worker.
- PODs nao alocados e seus motivos.
- Estatisticas gerais do escalonamento.
- Comparacao com o escalonador Kubernetes-like.

## Comparacao com Kubernetes-like

O escalonador `KubernetesLikeScheduler` representa a regra simplificada descrita
no enunciado: ele considera apenas CPU e memoria. Essa comparacao permite ver
casos em que um POD seria alocado pelo criterio padrao, mas produziria problemas
quando a simulacao tambem exige disco e latencia.

Na solucao proposta, um POD pode ser rejeitado mesmo havendo CPU e memoria
livres, caso nao exista disco suficiente ou caso a latencia media do Worker
ultrapasse o limite do POD. Essa decisao e mais conservadora, mas evita
alocacoes que violam metricas adicionais do ambiente.

## Observacao

Todos os dados sao simulados. A opcao `--seed` permite repetir exatamente a
mesma configuracao de Workers, PODs e latencias para comparacao e apresentacao.
