# 🕷️ Projeto de Extração de Dados do SISAB com Scrapy (API Síncrona)

## 1. Resumo 🎯

Este projeto utiliza o framework Scrapy (Python) para automatizar a extração de relatórios de produção do portal SISAB. A solução é exposta através de uma API síncrona construída com FastAPI, que permite a um usuário obter as datas disponíveis e solicitar um relatório diretamente.

O fluxo de trabalho é direto: uma rota para consultar as datas e outra para receber as datas escolhidas e retornar o arquivo CSV na mesma requisição.

## 2. Arquitetura do Projeto 🏗️

O projeto é composto por dois componentes principais que trabalham juntos:

### 2.1. Spiders (Scrapy)

-   **`DateFinderSpider` (`get_dates.py`):** Um spider simples cuja única função é acessar o portal do SISAB e extrair a lista de todas as competências (datas) disponíveis para consulta.
-   **`SisabSpider` (`sisab.py`):** O spider principal que realiza a extração. Ele é projetado para receber uma lista de datas e um caminho de arquivo como parâmetros, executar a extração completa e salvar o resultado no local especificado.

### 2.2. API (FastAPI)

A API (`main.py`) serve como a interface pública para o sistema. Ela orquestra a execução dos spiders de forma síncrona (bloqueante) para responder diretamente às requisições do usuário.

## 3. API Síncrona (FastAPI) ⚡

A API possui duas rotas principais que definem o fluxo de trabalho.

### ⚠️ Aviso Crítico sobre Timeouts

A rota `/iniciar-extracao` executa todo o processo de web scraping (que pode levar vários minutos) e só então retorna o arquivo. Plataformas de nuvem como o Render impõem um **limite de tempo (timeout)** para requisições HTTP (geralmente 30-60 segundos).

**Se a sua extração demorar mais do que esse limite, a conexão será cortada e o download falhará com um erro de timeout.** Esta arquitetura é ideal para extrações rápidas ou para uso em ambiente local. Para extrações longas em produção, uma arquitetura assíncrona (com tarefas em segundo plano) é recomendada.

### Lógica das Rotas

-   #### `GET /date-finder`
    -   **Função:** Retorna a lista de datas disponíveis no SISAB.
    -   **Lógica:** A API executa o `DateFinderSpider`, espera sua conclusão, coleta o resultado e o retorna como um array JSON.

-   #### `POST /iniciar-extracao`
    -   **Função:** Gera e retorna um relatório diretamente.
    -   **Lógica:** Recebe um array de datas no corpo da requisição. A API então executa o `SisabSpider`, passando as datas escolhidas. O spider salva o resultado em um arquivo temporário no servidor, e a API retorna esse arquivo diretamente para o usuário como um download na mesma requisição.

## 4. Como Executar 🚀

No terminal, navegue até a pasta `api_service` e execute:

```sh
uvicorn main:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`. A documentação interativa, onde você pode testar as rotas, pode ser acessada em `http://127.0.0.1:8000/docs`.

## 5. Fluxo de Trabalho 🔄

1.  **Obter as Datas:** Acesse a documentação (`/docs`) e execute a rota `GET /date-finder`. Você receberá uma lista de todas as datas disponíveis, como `["202405", "202404", ...]`. 

2.  **Gerar o Relatório:**
    -   Vá para a rota `POST /iniciar-extracao` na documentação.
    -   Clique em "Try it out".
    -   No campo "Request body", insira um array JSON com as datas que você deseja extrair. Exemplo:
        ```json
        [
          "202405",
          "202404"
        ]
        ```
    -   Clique em "Execute".
    -   **Aguarde.** A requisição ficará pendente enquanto o Scrapy trabalha. Quando a extração terminar, o download do arquivo `Relatorio-SISAB.csv` começará automaticamente no seu navegador.

## 6. Configuração ⚙️

As principais configurações de extração (como estados, tipos de equipe, etc.) são feitas diretamente no dicionário `form_data` dentro do arquivo `Scrapy_project/spiders/sisab.py`.
