import os
from pathlib import Path
import sys
from multiprocessing import Process, Queue

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import uvicorn

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import scrapy.signals

# Adiciona a pasta raiz ao path para garantir que os imports funcionem
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Scrapy_project.Scrapy_project.spiders.get_dates import DateFinderSpider
from Scrapy_project.Scrapy_project.spiders.sisab import SisabSpider

# --- Funções para executar os Spiders em Processos Separados ---

def run_date_finder_process(queue: Queue):
    """Executa o DateFinderSpider e coloca o resultado na fila."""
    try:
        crawled_items = []
        def item_scraped(item, response, spider):
            crawled_items.append(item)

        process = CrawlerProcess(get_project_settings())
        crawler = process.create_crawler(DateFinderSpider)
        crawler.signals.connect(item_scraped, signal=scrapy.signals.item_scraped)
        process.crawl(crawler)
        process.start()

        if crawled_items:
            queue.put(crawled_items[0])
        else:
            queue.put(None)
    except Exception as e:
        queue.put(e)

def run_sisab_process(queue: Queue, datas_alvo: list, output_file: str):
    """Executa o SisabSpider e sinaliza o sucesso/erro na fila."""
    try:
        process = CrawlerProcess(get_project_settings())
        process.crawl(SisabSpider, datas_alvo=datas_alvo, output_file=output_file)
        process.start()
        queue.put("SUCCESS")
    except Exception as e:
        queue.put(e)

# --- Lógica da API ---

app = FastAPI(
    title="API de Extração SISAB",
    version="5.4.4-redirect-home"
)

@app.get("/", summary="Redireciona para a Documentação", include_in_schema=False)
async def read_root():
    """
    Redireciona a rota raiz diretamente para a documentação interativa.
    """
    return RedirectResponse(url="/docs", status_code=302)

@app.get("/date-finder", summary="Retorna a lista de datas disponíveis no SISAB")
def get_available_dates():
    q = Queue()
    p = Process(target=run_date_finder_process, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if isinstance(result, Exception):
        raise HTTPException(status_code=500, detail=f"Falha ao buscar as datas: {result}")
    if not result:
        raise HTTPException(status_code=404, detail="Nenhuma data foi encontrada pelo spider.")

    datas = result.get("datas_disponiveis", [])
    return {"datas_disponiveis": datas}

@app.post("/iniciar-extracao", summary="Gera e retorna um relatório diretamente")
def start_extraction(datas_escolhidas: list[str]):
    if not datas_escolhidas:
        raise HTTPException(status_code=400, detail="A lista 'datas_escolhidas' não pode estar vazia.")

    # Define o caminho para a pasta de Downloads do usuário que está executando o servidor
    downloads_path = Path.home() / "Downloads"
    downloads_path.mkdir(parents=True, exist_ok=True)
    
    output_filename = "Relatorio-SISAB.csv"
    output_file_path = str(downloads_path / output_filename)

    try:
        q = Queue()
        p = Process(target=run_sisab_process, args=(q, datas_escolhidas, output_file_path))
        p.start()
        result = q.get()
        p.join()

        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Falha durante a extração: {result}")
        if result != "SUCCESS":
            raise HTTPException(status_code=500, detail=f"O processo de extração falhou com um resultado inesperado: {result}")

        return FileResponse(
            path=output_file_path,
            media_type='text/csv',
            filename=output_filename
        )
    except Exception as e:
        # Garante que qualquer outra exceção seja tratada como um erro do servidor
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado no servidor: {e}")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    uvicorn.run(app, host="0.0.0.0", port=8000)
