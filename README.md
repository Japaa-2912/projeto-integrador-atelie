# Sistema de Controle de Pedidos e Estoque - Ateliê Encanto

Trabalho do Projeto Integrador da disciplina Laboratório de Programação, do
curso de Engenharia de Software da UNISA.

Aluno: Davi Koseki Truzzi

O programa controla o catálogo de lembrancinhas personalizadas, os clientes, os
pedidos e o estoque. Foi feito em Python com SQLite e não usa nenhuma
biblioteca externa.

## Como rodar

Precisa do Python 3.10 ou mais novo.

```bash
cd programa
py main.py
```

Na primeira execução o programa cria o arquivo `dados/atelie.db` e coloca
alguns produtos e clientes de exemplo. Para começar do zero, apague esse
arquivo.

## Executável

O `dist/SistemaAtelie.exe` já está pronto e roda no Windows sem precisar
instalar Python. Para gerar de novo:

```bash
py -m pip install pyinstaller
py -m PyInstaller --onefile --name SistemaAtelie main.py
```

## Testes

```bash
cd programa
py -m unittest discover -s tests -t . -v
```

São 31 testes de regras de negócio, cálculos, relatórios e algoritmos.

## O que o programa faz

- Produtos: cadastro, edição, busca por nome (sem acento e sem diferenciar
  maiúscula), reposição de estoque e desativação.
- Clientes: cadastro, listagem e busca.
- Pedidos: abrir pedido, incluir e remover itens, aplicar desconto, finalizar
  (baixando o estoque) e cancelar (devolvendo o estoque).
- Relatórios: estoque baixo, mais vendidos, faturamento por categoria, vendas
  por período, resumo geral e exportação em CSV.

## Organização das pastas

- `main.py`: inicia o programa.
- `app/db.py`: conexão e tabelas do banco.
- `app/modelos.py`: classes Produto, Cliente, ItemPedido e ResumoPedido.
- `app/repositorios.py`: consultas SQL.
- `app/servicos.py`: regras de negócio.
- `app/relatorios.py`: relatórios e CSV.
- `app/algoritmos.py`: busca binária e ordenações.
- `app/utilidades.py`: conversão e formatação de valores.
- `app/interface.py`: menus do terminal.
- `tests/`: testes automatizados.

## Banco de dados

São cinco tabelas: `categorias`, `produtos`, `clientes`, `pedidos` e
`pedido_itens`.

Os preços ficam em centavos para não ter erro de arredondamento. Cada item do
pedido guarda o preço do momento da venda, então mudar o preço de um produto
depois não altera pedidos antigos. A finalização do pedido baixa o estoque e
muda o status na mesma transação.
