# Projeto de Extração de Dados do SISAB com Scrapy

## 1. Resumo

Este projeto utiliza o framework Scrapy (Python) para automatizar a extração de relatórios de produção do portal SISAB (Sistema de Informação em Saúde para a Atenção Básica). A solução foi desenhada para ser modular, superando o desafio de interagir com uma página dinâmica que exige múltiplos passos para a obtenção dos dados.

O objetivo principal é automatizar o download de arquivos CSV, selecionando dinamicamente as competências (datas) de interesse e configurando múltiplos filtros, como estados, tipos de equipe e categorias profissionais.

## 2. Arquitetura Modular e Lógica de Herança

A característica principal deste projeto é sua arquitetura modular, que promove a separação de responsabilidades e a reutilização de código. Isso é alcançado através de uma estrutura com dois spiders e o uso de herança.

### 2.1. `DateFinderSpider` (`get_dates.py`)

Este é o **spider base**. Sua única responsabilidade é conectar-se ao portal do SISAB e extrair a lista completa de todas as competências (datas) disponíveis para consulta. Ele funciona como um "provedor de datas" para outros spiders.

- **Função:** Acessar a página e obter a lista de datas.
- **Independência:** Pode ser executado de forma independente (`scrapy crawl date_finder`) para uma verificação rápida das datas disponíveis no portal.

### 2.2. `SisabSpider` (`sisab.py`)

Este é o **spider principal**, responsável pela extração de fato. Ele contém a lógica de negócio para baixar os relatórios.

- **Função:** Filtrar as datas de interesse, montar a requisição POST com todos os parâmetros necessários e salvar o arquivo CSV resultante.
- **Lógica de Negócio:** É neste spider que se configura a lista `datas_alvo` (os períodos que se deseja baixar) e todos os outros filtros do relatório.

### 2.3. A Lógica de Herança

Para conectar os dois spiders, utilizamos o conceito de **herança** do Python:

```python
# Em sisab.py
from .get_dates import DateFinderSpider

class SisabSpider(DateFinderSpider):
    # ... código do spider principal
```

**Como funciona o fluxo:**

1.  Ao executar `scrapy crawl sisab`, o Scrapy inicia o `SisabSpider`.
2.  Como `SisabSpider` **herda** de `DateFinderSpider`, ele automaticamente ganha todos os seus métodos, incluindo o `start_requests`.
3.  O `start_requests` do `DateFinderSpider` é executado, fazendo a primeira requisição à página.
4.  Após a página ser baixada, o método `parse_page` do spider base extrai a lista de todas as datas disponíveis.
5.  Em seguida, ele chama o método `process_dates(response, dates)`, que foi projetado para ser implementado pelo spider filho.
6.  O `SisabSpider` implementa sua própria versão do `process_dates`. É aqui que a "mágica" acontece: ele recebe a lista completa de datas, aplica seus próprios filtros (`datas_alvo`), monta a requisição POST complexa e dispara o processo de download.

Essa abordagem garante que o `SisabSpider` não precisa saber *como* obter as datas, ele apenas as recebe e decide *o que fazer* com elas. Se a forma de obter as datas no site mudar no futuro, apenas o `DateFinderSpider` precisará ser atualizado.

## 3. Como Executar

**Pré-requisitos:**
- Python 3.x
- Scrapy (`pip install scrapy`)

**Executando o spider principal:**

Para realizar a extração completa e salvar os arquivos CSV, execute:

```sh
scrapy crawl sisab
```

Os arquivos serão salvos no diretório configurado no método `save_csv` (atualmente `C:\Users\CintraMan\Downloads`).

**Executando o spider base:**

Para apenas listar as datas disponíveis no portal, execute:

```sh
scrapy crawl date_finder
```

## 4. Configuração

As principais configurações são feitas no arquivo `Scrapy_project/spiders/sisab.py`:

-   **`datas_alvo`**: Modifique esta lista para definir quais períodos (ano/mês) você deseja extrair.
-   **Filtros do Formulário**: Dentro do método `process_dates`, o dicionário `form_data` contém todos os filtros enviados na requisição, como `estados`, `categoriaProfissional`, etc. Eles podem ser ajustados conforme a necessidade.
