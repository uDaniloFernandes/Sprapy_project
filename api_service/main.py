import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn

# --- Configuração e Simulação de Componentes ---

#  uvicorn main:app --reload

app = FastAPI(
    title="API de Extração SISAB",
    description="Uma API para iniciar, monitorar e baixar relatórios do SISAB.",
    version="1.0.0"
)

# 1. Caminho de Armazenamento Compartilhado (CORRIGIDO)
SHARED_STORAGE_PATH = os.path.join(os.path.expanduser('~'), "Downloads")

# 2. Simulação de um Banco de Dados em Memória
fake_db = {}

# 3. Simulação de uma Fila de Tarefas
fake_task_queue = []

# --- Endpoints da API ---

@app.get("/", summary="Rota de Boas-Vindas")
async def read_root():
    """
    Retorna uma mensagem de boas-vindas e direciona para a documentação da API.
    """
    return {
        "mensagem": "Bem-vindo à API de Extração de Dados do SISAB!",
        "documentacao_interativa": "/docs"
    }

@app.post("/iniciar-extracao", status_code=202, summary="Inicia um novo processo de extração")
async def iniciar_extracao():
    """
    Agenda uma nova tarefa de extração de dados do SISAB.

    - Gera um ID de tarefa único.
    - Adiciona a tarefa a uma fila para ser processada pelo worker Scrapy.
    - Armazena o estado inicial da tarefa no banco de dados.
    - Retorna imediatamente o ID da tarefa para o cliente.
    """
    task_id = str(uuid.uuid4())
    
    # Adiciona a tarefa na fila (o worker Scrapy pegaria daqui)
    fake_task_queue.append(task_id)
    
    # Salva o estado inicial no banco de dados
    fake_db[task_id] = {
        "status": "PENDENTE",
        "error_message": None,
        "download_url": None
    }
    
    print(f"Tarefa {task_id} adicionada à fila. Status: PENDENTE.")
    
    return {
        "mensagem": "Processo de extração agendado com sucesso!",
        "task_id": task_id,
        "status_url": f"/status/{task_id}"
    }

@app.get("/status/{task_id}", summary="Verifica o status de uma tarefa de extração")
async def get_status(task_id: str):
    """
    Consulta o banco de dados para retornar o estado atual de uma tarefa.
    """
    task = fake_db.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    if task["status"] == "ERRO":
        return {
            "task_id": task_id,
            "status": "ERRO",
            "mensagem": "A extração falhou.",
            "detalhes_do_erro": task["error_message"]
        }

    if task["status"] == "CONCLUIDO":
        return {
            "task_id": task_id,
            "status": "CONCLUIDO",
            "mensagem": "Sua extração foi concluída com sucesso!",
            "download_url": f"/download/{task_id}"
        }

    return {"task_id": task_id, "status": task["status"]}

@app.get("/download/{task_id}", response_class=FileResponse, summary="Baixa o arquivo de resultado")
async def download_file(task_id: str):
    """
    Serve o arquivo CSV final para download, após verificar se a tarefa foi concluída.
    """
    task = fake_db.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    # if task["status"] != "CONCLUIDO":
    #     raise HTTPException(
    #         status_code=409,  # Conflict
    #         detail=f"Não é possível baixar o arquivo. Status atual da tarefa: {task['status']}."
    #     )

    file_path = os.path.join(SHARED_STORAGE_PATH, f"Relatorio-SISAB_{task_id}.csv")

    if not os.path.exists(file_path):
        # Este erro indica uma inconsistência entre o DB e o sistema de arquivos.
        raise HTTPException(status_code=500, detail="Erro interno: O arquivo de resultado não foi encontrado no disco.")

    return FileResponse(path=file_path, media_type='text/csv', filename=f"relatorio_{task_id}.csv")

# --- Bloco de Execução ---

if __name__ == "__main__":
    print(f"API iniciada. O armazenamento compartilhado está configurado para: {SHARED_STORAGE_PATH}")
    print("Para executar, use o comando: uvicorn main:app --reload")
    uvicorn.run(app, host="127.0.0.1", port=8000)
