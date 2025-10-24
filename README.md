# 🕷️ Projeto de Extração de Dados do SISAB com Scrapy

## 1. Resumo 🎯

Este projeto utiliza o framework Scrapy (Python) para automatizar a extração de relatórios de produção do portal SISAB. A solução foi desenhada para ser robusta e modular, e inclui uma API de gerenciamento (FastAPI) que orquestra e executa o processo de web scraping de forma assíncrona.

O objetivo é permitir que um usuário solicite uma extração de dados através de uma API, acompanhe o progresso e baixe o arquivo final, com a API gerenciando todo o ciclo de vida da extração.

## 2. Arquitetura do Scrapy 🧱

A característica principal do processo de extração é sua arquitetura modular, que promove a separação de responsabilidades e a reutilização de código.

### 2.1. `DateFinderSpider` (`get_dates.py`) 📅

Este é o **spider base**. Sua única responsabilidade é conectar-se ao portal do SISAB e extrair a lista completa de todas as competências (datas) disponíveis para consulta. Ele funciona como um "provedor de datas" para outros spiders.

### 2.2. `SisabSpider` (`sisab.py`) 📥

Este é o **spider principal**, responsável pela extração de fato. Ele herda a capacidade de obter datas do `DateFinderSpider` e implementa a lógica de negócio para baixar os relatórios, como filtrar as datas de interesse e montar a requisição final.

### 2.3. A Lógica de Herança 🧬

O `SisabSpider` herda do `DateFinderSpider`, o que permite que ele reutilize a lógica de conexão e obtenção de datas. Ao ser iniciado pela API, o `start_requests` do spider base é chamado, e as datas encontradas são passadas para o método `process_dates` do spider principal, que continua a execução.

## 3. API de Gerenciamento (FastAPI) 👩‍💼

Para orquestrar o processo de extração, o projeto inclui uma API construída com FastAPI. Esta API atua como uma "gerente de tarefas" que recebe pedidos, **inicia e supervisiona a execução do Scrapy em segundo plano**, e entrega o resultado final ao usuário.

**A API executa o Scrapy diretamente em um thread separado**, garantindo que a API permaneça responsiva.

### Lógica das Rotas

-   #### `GET /`
    -   **Função:** Rota de boas-vindas. Redireciona para a documentação interativa da API (`/docs`), servindo como ponto de partida.

-   #### `POST /iniciar-extracao`
    -   **Função:** Inicia um novo trabalho de extração.
    -   **Lógica:** Esta rota gera um identificador único para a tarefa (`task_id`), armazena o status inicial como `PENDENTE` no banco de dados e **inicia a execução do `SisabSpider` em um thread separado**. A API responde **imediatamente** ao usuário, retornando o `task_id`.

-   #### `GET /status/{task_id}`
    -   **Função:** Verifica o progresso de um trabalho de extração.
    -   **Lógica:** O usuário fornece o `task_id`. A API consulta seu banco de dados e retorna o status atual da tarefa (ex: `PENDENTE`, `EM_PROGRESSO`, `CONCLUIDO` ou `ERRO`).

-   #### `GET /download/{task_id}`
    -   **Função:** Entrega o arquivo CSV final.
    -   **Lógica:** Esta rota verifica o status da tarefa no banco de dados. Se a tarefa estiver `CONCLUIDO`, ela verifica se um arquivo com o nome `Relatorio-SISAB_{task_id}.csv` existe no disco persistente (criado pelo spider Scrapy). Se o arquivo existir, a API o serve para o usuário, iniciando o download no navegador.

## 4. Como Executar o Sistema 🚀

### 4.1. Executando a API (Localmente)

No terminal, navegue até a pasta `api_service` e execute:

```sh
uvicorn main:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`. A documentação interativa pode ser acessada em `http://127.0.0.1:8000/docs`.

### 4.2. Executando a Extração (Scrapy Localmente, para Teste)

Para testar o spider Scrapy de forma isolada (sem a API), navegue até a pasta `Scrapy_project` e execute:

```sh
scrapy crawl sisab
```

Este comando fará o spider rodar e salvará um arquivo com um ID aleatório na sua pasta de Downloads.

## 5. Fluxo de Trabalho Completo (Usando a API) 🔄

Este guia mostra como usar a API para iniciar e gerenciar uma extração.

1.  **Inicie a API** conforme as instruções acima.

2.  **Inicie uma Extração:** Acesse a documentação (`/docs`), execute a rota `POST /iniciar-extracao` e **copie o `task_id`** retornado.

3.  **Monitore o Status:** Use a rota `GET /status/{task_id}` (na documentação ou diretamente no navegador) para verificar o progresso. O status mudará de `PENDENTE` para `EM_PROGRESSO` e, finalmente, para `CONCLUIDO` (ou `ERRO`).

4.  **Faça o Download:** Quando o status for `CONCLUIDO`, use a rota `GET /download/{task_id}` (na documentação ou diretamente no navegador) para baixar o arquivo CSV. O download do arquivo deve começar imediatamente.

## 6. Configuração ⚙️

As principais configurações de extração são feitas no arquivo `Scrapy_project/Scrapy_project/spiders/sisab.py`:

-   **`datas_alvo`**: Modifique esta lista para definir quais períodos (ano/mês) você deseja extrair.
-   **Filtros do Formulário**: Dentro do método `process_dates`, o dicionário `form_data` contém todos os filtros enviados na requisição.
