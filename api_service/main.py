import os
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import uvicorn

# Importa componentes do Scrapy e Crochet
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from crochet import setup, wait_for

# Inicia o Crochet para permitir rodar Scrapy em um contexto não-Twisted
setup()

# Importa os spiders diretamente
from Scrapy_project.Scrapy_project.spiders.get_dates import DateFinderSpider
from Scrapy_project.Scrapy_project.spiders.sisab import SisabSpider

# --- Lógica da API ---

app = FastAPI(
    title="API de Extração SISAB (Síncrona)",
    description="Uma API com duas rotas para obter datas e gerar relatórios diretamente.",
    version="5.0.0-synchronous"
)

@app.get("/", summary="Redireciona para a Documentação", include_in_schema=False)
async def read_root():
    return RedirectResponse(url="/docs")

# --- Rota 1: Obter Datas Disponíveis ---
@app.get("/date-finder", summary="Retorna a lista de datas disponíveis no SISAB")
def get_available_dates():
    """
    Executa o DateFinderSpider de forma síncrona para buscar e retornar
    a lista de competências (datas) disponíveis no portal do SISAB.
    Esta operação é relativamente rápida.
    """
    try:
        # Coleta os itens que o spider produzir
        crawled_items = []

        @wait_for(timeout=60.0) # Timeout de 60 segundos para esta operação
        def run_spider():
            runner = CrawlerRunner(get_project_settings())
            deferred = runner.crawl(DateFinderSpider)
            # Adiciona um callback para coletar os itens quando o spider terminar
            deferred.addCallback(lambda _: crawled_items.extend(DateFinderSpider.items))
            return deferred

        # Executa a função e espera a conclusão
        run_spider()

        # Verifica se algum item foi coletado
        if not crawled_items:
            raise HTTPException(status_code=404, detail="Nenhuma data foi encontrada pelo spider.")

        # Retorna os dados do primeiro item coletado
        datas = crawled_items[0].get("datas_disponiveis", [])
        return {"datas_disponiveis": datas}

    except Exception as e:
        # Captura erros de timeout do Crochet ou outras falhas
        raise HTTPException(status_code=500, detail=f"Falha ao buscar as datas: {e}")


# --- Rota 2: Iniciar Extração e Retornar Relatório ---
@app.post("/iniciar-extracao", summary="Gera e retorna um relatório diretamente")
def start_extraction(datas_escolhidas: list[str]):
    """
    **AVISO:** Esta rota executa todo o processo de scraping e só então retorna o arquivo.
    Pode falhar com um erro de **timeout** em ambientes de produção se a extração demorar mais de 30-60 segundos.

    Recebe uma lista de datas, executa a extração e retorna o arquivo CSV para download.
    """
    if not datas_escolhidas:
        raise HTTPException(status_code=400, detail="A lista 'datas_escolhidas' não pode estar vazia.")

    # Usa um arquivo temporário para salvar o resultado do Scrapy
    with tempfile.NamedTemporaryFile(delete=True, suffix=".csv", mode='w+b') as temp_file:
        temp_file_path = temp_file.name
        try:
            @wait_for(timeout=1800.0) # Timeout longo de 30 minutos (pode não ser respeitado pela plataforma de nuvem)
            def run_spider():
                runner = CrawlerRunner(get_project_settings())
                # Passa as datas escolhidas e o caminho do arquivo de saída para o spider
                return runner.crawl(SisabSpider, datas_alvo=datas_escolhidas, output_file=temp_file_path)

            # Executa o spider e espera a conclusão
            run_spider()

            # Retorna o arquivo temporário como uma resposta para download
            return FileResponse(
                path=temp_file_path,
                media_type='text/csv',
                filename="Relatorio-SISAB.csv"
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Falha durante a extração: {e}")

# --- Bloco de Execução ---

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
