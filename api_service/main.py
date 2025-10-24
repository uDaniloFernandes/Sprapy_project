import os
import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import uvicorn
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Importa componentes do Scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Importa o spider diretamente
# Certifique-se de que o caminho do import está correto em relação à raiz do projeto
from Scrapy_project.Scrapy_project.spiders.sisab import SisabSpider

# --- Configuração para a Nuvem (Render) ---

# 1. Conexão com o Banco de Dados
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("AVISO: Variável de ambiente DATABASE_URL não encontrada. Usando DB SQLite local para testes.")
    DATABASE_URL = "sqlite:///./local_test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Caminho para o Disco Persistente
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
Base.metadata.create_all(bind=engine)


# --- Lógica da API ---

app = FastAPI(
    title="API de Extração SISAB (Monolítica)",
    description="Uma API que inicia, monitora e baixa relatórios do SISAB, executando o Scrapy diretamente.",
    version="3.0.0-monolithic"
)

@app.get("/", summary="Redireciona para a Documentação")
async def read_root():
    return RedirectResponse(url="/docs")

# --- Função para rodar o Scrapy em background ---
def _run_scrapy_in_background(task_id: str):
    """
    Esta função executa o spider Scrapy e atualiza o status da tarefa no DB.
    Ela é executada em um thread separado para não bloquear o loop de eventos da API.
    """
    db = SessionLocal()
    try:
        # Atualiza o status para EM_PROGRESSO
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = "EM_PROGRESSO"
            db.commit()
            print(f"Tarefa {task_id} atualizada para EM_PROGRESSO.")

        # Configura e inicia o processo do Scrapy
        settings = get_project_settings()
        # É preciso configurar o Scrapy para não interferir com o loop de eventos do asyncio da API
        settings.set("TWISTED_REACTOR", "twisted.internet.asyncioreactor.AsyncioSelectorReactor")
        process = CrawlerProcess(settings)
        process.crawl(SisabSpider, task_id=task_id)
        process.start() # O script fica bloqueado aqui até o spider terminar

        # Se o spider terminou sem exceções, atualiza o status para CONCLUIDO
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = "CONCLUIDO"
            db.commit()
            print(f"Tarefa {task_id} concluída com sucesso.")

    except Exception as e:
        # Captura qualquer erro durante a execução do Scrapy
        print(f"ERRO na execução do Scrapy para a tarefa {task_id}: {e}")
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = "ERRO"
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


@app.post("/iniciar-extracao", status_code=202, summary="Inicia um novo processo de extração")
async def iniciar_extracao():
    """
    Agenda uma nova tarefa de extração e a inicia em segundo plano.
    """
    db = SessionLocal()
    try:
        task_id = str(uuid.uuid4())
        new_task = Task(task_id=task_id, status="PENDENTE")
        db.add(new_task)
        db.commit()
        print(f"Tarefa {task_id} adicionada ao banco de dados. Status: PENDENTE.")

        # Inicia a execução do Scrapy em um thread separado para não bloquear a API
        asyncio.create_task(asyncio.to_thread(_run_scrapy_in_background, task_id))
        
        return {
            "mensagem": "Processo de extração agendado e iniciado em segundo plano!",
            "task_id": task_id,
            "status_url": f"/status/{task_id}"
        }
    finally:
        db.close()

@app.get("/status/{task_id}", summary="Verifica o status de uma tarefa de extração")
async def get_status(task_id: str):
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
        elif task.status == "CONCLUIDO":
            response_data["mensagem"] = "Sua extração foi concluída com sucesso!"
            response_data["download_url"] = f"/download/{task_id}"
        else: # PENDENTE ou EM_PROGRESSO
            response_data["mensagem"] = "Sua extração está em andamento ou aguardando."

        return response_data
    finally:
        db.close()

@app.get("/download/{task_id}", response_class=FileResponse, summary="Baixa o arquivo de resultado")
async def download_file(task_id: str):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

        if task.status != "CONCLUIDO":
            raise HTTPException(
                status_code=409,
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
