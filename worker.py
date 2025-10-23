import os
import time
import subprocess
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# --- Configuração e Conexão com o Banco de Dados ---

# Pega a URL de conexão do banco de dados a partir das variáveis de ambiente (fornecida pelo Render)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Modelo da Tabela de Tarefas ---
# Esta definição deve ser idêntica à da API para que ambos conversem com a mesma tabela.
class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="PENDENTE")
    error_message = Column(Text, nullable=True)


# --- Lógica do Worker ---

def run_scrapy_task(task_id: str):
    """
    Executa o spider Scrapy como um processo separado, passando o task_id.
    Atualiza o status da tarefa no banco de dados com base no resultado.
    """
    print(f"Iniciando spider para a tarefa: {task_id}")
    try:
        # Constrói e executa o comando 'scrapy crawl'
        # O 'cwd' (current working directory) é crucial para dizer ao Scrapy onde encontrar seu projeto.
        subprocess.run(
            ["scrapy", "crawl", "sisab", "-a", f"task_id={task_id}"],
            check=True,  # Levanta um erro se o Scrapy retornar um código de saída diferente de 0
            capture_output=True,  # Captura a saída para logar em caso de erro
            text=True,
            cwd="./Scrapy_project"  # Aponta para a pasta do projeto Scrapy
        )

        # Se o subprocesso terminou sem erros, marca a tarefa como concluída
        db = SessionLocal()
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = "CONCLUIDO"
            db.commit()
            print(f"Tarefa {task_id} concluída com sucesso.")
        db.close()

    except subprocess.CalledProcessError as e:
        # Se o Scrapy falhou (retornou um erro), atualiza o status para ERRO
        error_output = e.stderr or e.stdout
        print(f"ERRO ao executar a tarefa {task_id}: {error_output}")
        db = SessionLocal()
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = "ERRO"
            task.error_message = error_output
            db.commit()
        db.close()


def main_loop():
    """
    Loop principal do worker. Fica verificando o banco de dados por novas tarefas.
    """
    print("Worker iniciado. Procurando por tarefas pendentes...")
    while True:
        db = SessionLocal()
        try:
            # Procura pela primeira tarefa com status "PENDENTE"
            pending_task = db.query(Task).filter(Task.status == "PENDENTE").first()

            if pending_task:
                # Se encontrou, atualiza o status para "EM_PROGRESSO" para evitar que outro worker a pegue
                print(f"Tarefa {pending_task.task_id} encontrada. Iniciando processamento.")
                pending_task.status = "EM_PROGRESSO"
                db.commit()

                # Executa a tarefa
                run_scrapy_task(pending_task.task_id)
            else:
                # Se não encontrou nenhuma tarefa, espera 10 segundos antes de verificar novamente
                time.sleep(10)
        finally:
            db.close()


if __name__ == "__main__":
    main_loop()