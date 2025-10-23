import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import uvicorn
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# --- Configuração para a Nuvem (Render) ---

# 1. Conexão com o Banco de Dados
# O Render fornecerá a URL do banco de dados na variável de ambiente DATABASE_URL.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Se a variável não estiver definida, o app não pode funcionar na nuvem.
    # Para testes locais, você poderia apontar para um db local, ex: "sqlite:///./test.db"
    print("AVISO: Variável de ambiente DATABASE_URL não encontrada. Usando DB em memória para testes locais.")
    DATABASE_URL = "sqlite:///./local_test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Caminho para o Disco Persistente
# O Render fornecerá o caminho do disco na variável RENDER_DISK_PATH.
# Para testes locais, o padrão continua sendo a pasta Downloads.
SHARED_STORAGE_PATH = os.environ.get("RENDER_DISK_PATH", os.path.join(os.path.expanduser('~'), "Downloads"))


# --- Modelo do Banco de Dados (SQLAlchemy ORM) ---

class Task(Base):
    """
    Esta classe define a estrutura da tabela 'tasks' no banco de dados.
    """
    __tablename__ = "tasks"
    task_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="PENDENTE")
    error_message = Column(Text, nullable=True)

# Cria a tabela no banco de dados, se ela ainda não existir.
# Isso é executado uma vez quando a API inicia.
Base.metadata.create_all(bind=engine)


# --- Lógica da API ---

app = FastAPI(
    title="API de Extração SISAB",
    description="Uma API para iniciar, monitorar e baixar relatórios do SISAB.",
    version="2.0.0-cloud"
)

@app.get("/", summary="Redireciona para a Documentação")
async def read_root():
    """
    Redireciona a rota raiz diretamente para a documentação interativa.
    """
    return RedirectResponse(url="/docs")

@app.post("/iniciar-extracao", status_code=202, summary="Inicia um novo processo de extração")
async def iniciar_extracao():
    """
    Agenda uma nova tarefa de extração de dados do SISAB.
    Cria um novo registro na tabela 'tasks' com o status 'PENDENTE'.
    """
    db = SessionLocal()
    try:
        task_id = str(uuid.uuid4())
        new_task = Task(task_id=task_id, status="PENDENTE")
        db.add(new_task)
        db.commit()
        print(f"Tarefa {task_id} adicionada ao banco de dados. Status: PENDENTE.")
        return {
            "mensagem": "Processo de extração agendado com sucesso!",
            "task_id": task_id,
            "status_url": f"/status/{task_id}"
        }
    finally:
        db.close()

@app.get("/status/{task_id}", summary="Verifica o status de uma tarefa de extração")
async def get_status(task_id: str):
    """
    Consulta o banco de dados para retornar o estado atual de uma tarefa.
    """
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()

        if not task:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

        response_data = {
            "task_id": task.task_id,
            "status": task.status
        }

        if task.status == "ERRO":
            response_data["mensagem"] = "A extração falhou."
            response_data["detalhes_do_erro"] = task.error_message
        
        if task.status == "CONCLUIDO":
            response_data["mensagem"] = "Sua extração foi concluída com sucesso!"
            response_data["download_url"] = f"/download/{task_id}"

        return response_data
    finally:
        db.close()

@app.get("/download/{task_id}", response_class=FileResponse, summary="Baixa o arquivo de resultado")
async def download_file(task_id: str):
    """
    Serve o arquivo CSV final para download, após verificar o status no banco de dados.
    """
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()

        if not task:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

        if task.status != "CONCLUIDO":
            raise HTTPException(
                status_code=409,  # Conflict
                detail=f"Não é possível baixar o arquivo. Status atual da tarefa: {task.status}."
            )
    finally:
        db.close()

    file_path = os.path.join(SHARED_STORAGE_PATH, f"Relatorio-SISAB_{task_id}.csv")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Erro interno: O arquivo de resultado não foi encontrado no disco.")

    return FileResponse(path=file_path, media_type='text/csv', filename=f"relatorio_{task_id}.csv")

# --- Bloco de Execução ---

if __name__ == "__main__":
    print(f"API iniciada. O armazenamento compartilhado está configurado para: {SHARED_STORAGE_PATH}")
    # O host '0.0.0.0' é necessário para que a API seja acessível de fora do contêiner do Render.
    uvicorn.run(app, host="0.0.0.0", port=8000)
