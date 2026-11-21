# Sistema de Controle de Pedidos e Estoque — Ateliê Encanto

Programa de linha de comando desenvolvido em **Python 3** com banco de dados
**SQLite**, para o Projeto Integrador da disciplina *Laboratório de Programação*.

Autor: **Davi Koseki Truzzi** — Engenharia de Software, Universidade Santo Amaro (UNISA).

O sistema controla o catálogo de lembrancinhas personalizadas, o cadastro de
clientes, a montagem de pedidos e a baixa automática de estoque, além de gerar
relatórios gerenciais.

## Requisitos

- Python 3.10 ou superior (testado com Python 3.12)
- Nenhuma biblioteca externa: o projeto usa apenas a biblioteca padrão

## Como executar

```bash
cd programa
py main.py
```

Na primeira execução o arquivo `dados/atelie.db` é criado automaticamente e
preenchido com um catálogo de exemplo. Para começar do zero, apague esse arquivo.

Também é possível gerar um executável independente:

```bash
py -m pip install pyinstaller
py -m PyInstaller --onefile --name SistemaAtelie main.py
```

O arquivo `dist/SistemaAtelie.exe` roda em qualquer computador Windows sem
Python instalado.

## Como executar os testes automatizados

```bash
cd programa
py -m unittest discover -s tests -t . -v
```

São 31 testes cobrindo regras de negócio, cálculos, validações, relatórios e
algoritmos de busca e ordenação.

## Funcionalidades

| Módulo | Recursos |
| --- | --- |
| Produtos | cadastro, edição, busca por nome (ignora acento e maiúscula), reposição de estoque, desativação |
| Clientes | cadastro, listagem e busca por nome |
| Pedidos | abertura, inclusão e remoção de itens, desconto, finalização com baixa de estoque, cancelamento com devolução |
| Relatórios | estoque baixo, produtos mais vendidos, faturamento por categoria, vendas por período, resumo geral, exportação em CSV |

## Estrutura do projeto

```
programa/
├── main.py                 # ponto de entrada
├── app/
│   ├── db.py               # conexão e esquema do banco
│   ├── modelos.py          # classes de domínio (Produto, Cliente, Pedido...)
│   ├── repositorios.py     # consultas SQL
│   ├── servicos.py         # regras de negócio e transações
│   ├── relatorios.py       # relatórios e exportação CSV
│   ├── algoritmos.py       # busca binária e ordenações
│   ├── utilidades.py       # formatação e conversão de valores
│   └── interface.py        # menus e entrada de dados
├── tests/                  # testes automatizados
├── dados/                  # banco SQLite (criado em tempo de execução)
└── relatorios/             # arquivos CSV exportados
```

## Modelo de dados

```
categorias (1) ──< produtos (1) ──< pedido_itens >── (1) pedidos >── (1) clientes
```

- `categorias`: agrupamento do catálogo.
- `produtos`: nome, categoria, preço em centavos, estoque atual e estoque mínimo.
- `clientes`: nome, telefone e cidade.
- `pedidos`: cliente, status (ABERTO, FINALIZADO, CANCELADO) e desconto.
- `pedido_itens`: produto, quantidade e preço unitário **no momento da venda**.

## Decisões de projeto

- **Valores em centavos**: preços são inteiros para evitar erros de
  arredondamento de ponto flutuante.
- **Preço congelado no item**: alterar o preço de um produto não muda pedidos
  já registrados.
- **Transações**: a finalização do pedido baixa o estoque e altera o status na
  mesma transação; qualquer falha desfaz tudo.
- **Regras no banco**: restrições `CHECK` impedem estoque negativo e desconto
  fora de 0–100.
- **Campo `nome_busca`**: versão do nome sem acentos e em minúsculas, indexada,
  para busca rápida e tolerante a acentuação.
