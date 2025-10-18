# 🕷️ Projeto de Extração de Dados do SISAB com Scrapy

## 1. Resumo 🎯

Este projeto utiliza o framework Scrapy (Python) para automatizar a extração de relatórios de produção do portal SISAB. A solução foi desenhada para ser robusta e modular, e inclui uma API de gerenciamento (FastAPI) para controlar o processo de extração de forma assíncrona.

O objetivo é permitir que um usuário solicite uma extração de dados através de uma API, acompanhe o progresso e baixe o arquivo final sem interagir diretamente com o processo de web scraping.

## 2. Arquitetura do Scrapy 🧱

A característica principal do processo de extração é sua arquitetura modular, que promove a separação de responsabilidades e a reutilização de código.

### 2.1. `DateFinderSpider` (`get_dates.py`) 📅

Este é o **spider base**. Sua única responsabilidade é conectar-se ao portal do SISAB e extrair a lista completa de todas as competências (datas) disponíveis para consulta. Ele funciona como um "provedor de datas" para outros spiders.

### 2.2. `SisabSpider` (`sisab.py`) 📥

Este é o **spider principal**, responsável pela extração de fato. Ele herda a capacidade de obter datas do `DateFinderSpider` e implementa a lógica de negócio para baixar os relatórios, como filtrar as datas de interesse e montar a requisição final.

### 2.3. A Lógica de Herança 🧬

O `SisabSpider` herda do `DateFinderSpider`, o que permite que ele reutilize a lógica de conexão e obtenção de datas. Ao executar `scrapy crawl sisab`, o `start_requests` do spider base é chamado, e as datas encontradas são passadas para o método `process_dates` do spider principal, que continua a execução.

## 3. API de Gerenciamento (FastAPI) 👩‍💼

Para orquestrar o processo de extração, o projeto inclui uma API construída com FastAPI. A API atua como uma "gerente de tarefas", recebendo pedidos, delegando o trabalho pesado para o Scrapy e entregando o resultado final ao usuário.

**A API não executa a extração diretamente.** Ela gerencia um fluxo de trabalho assíncrono.

### Lógica das Rotas

-   #### `GET /`
    -   **Função:** Rota de boas-vindas. Retorna uma mensagem simples e um link para a documentação interativa da API (`/docs`), servindo como ponto de partida para qualquer usuário.

-   #### `POST /iniciar-extracao`
    -   **Função:** Inicia um novo trabalho de extração.
    -   **Lógica:** Esta rota **não** espera a extração terminar. Ela gera um identificador único para a tarefa (`task_id`), armazena o status inicial como `PENDENTE` e responde **imediatamente** ao usuário, retornando o `task_id`. Em um sistema de produção, ela publicaria este `task_id` em uma fila de tarefas.

-   #### `GET /status/{task_id}`
    -   **Função:** Verifica o progresso de um trabalho de extração.
    -   **Lógica:** O usuário fornece o `task_id` recebido anteriormente. A API consulta seu banco de dados interno e retorna o status atual da tarefa (ex: `PENDENTE`, `CONCLUIDO` ou `ERRO`).

-   #### `GET /download/{task_id}`
    -   **Função:** Entrega o arquivo CSV final.
    -   **Lógica:** Esta rota **não** realiza o download do site do SISAB. Ela apenas verifica se um arquivo com o nome `Relatorio-SISAB_{task_id}.csv` já existe no disco (criado pelo spider Scrapy). Se o arquivo existir, a API o serve para o usuário, iniciando o download no navegador.

## 4. Como Executar o Sistema 🚀

### 4.1. Executando a API de Gerenciamento

No terminal, navegue até a pasta `api_service` e execute:

```sh
uvicorn main:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`. A documentação interativa pode ser acessada em `http://127.0.0.1:8000/docs`.

### 4.2. Executando a Extração (Scrapy)

Para executar o spider de forma independente (sem a API), navegue até a pasta `Scrapy_project` e execute:

```sh
scrapy crawl sisab
```

Para conectar a execução do Scrapy a uma tarefa da API, veja o fluxo de trabalho abaixo.

## 5. Fluxo de Trabalho Completo (Simulação) 🔄

Este guia simula como a API e o Scrapy trabalham juntos.

1.  **Inicie a API** conforme as instruções acima.

2.  **Agende uma Tarefa:** Acesse a documentação (`/docs`), execute a rota `POST /iniciar-extracao` e **copie o `task_id`** retornado.

3.  **Execute o Worker (Scrapy):** Em outro terminal, na pasta `Scrapy_project`, execute o spider passando o `task_id` que você copiou. Este comando diz ao Scrapy para trabalhar em uma tarefa específica:

    ```sh
    # Substitua {SUA_TASK_ID} pelo ID que você copiou
    scrapy crawl sisab -a task_id={SUA_TASK_ID}
    ```

4.  **Aguarde o Fim:** O Scrapy irá executar a extração e salvar o arquivo na sua pasta de Downloads com o nome `Relatorio-SISAB_{SUA_TASK_ID}.csv`.

5.  **Faça o Download pela API:** Agora que o arquivo existe, acesse a rota de download no seu navegador, usando a mesma `task_id`:

    ```
    http://127.0.0.1:8000/download/{SUA_TASK_ID}
    ```

    O download do arquivo CSV deve começar imediatamente.

## 6. Configuração ⚙️

As principais configurações de extração são feitas no arquivo `Scrapy_project/spiders/sisab.py`:

-   **`datas_alvo`**: Modifique esta lista para definir quais períodos (ano/mês) você deseja extrair.
-   **Filtros do Formulário**: Dentro do método `process_dates`, o dicionário `form_data` contém todos os filtros enviados na requisição.
