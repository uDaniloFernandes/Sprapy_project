import scrapy
import os

class DateFinderSpider(scrapy.Spider):
    name = "date_finder"

    def start_requests(self):
        """
        Faz o primeiro GET para a página de relatórios.
        """
        url = "https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        yield scrapy.Request(url=url, callback=self.parse_dates)

    def parse_dates(self, response):
        """
        Extrai as datas disponíveis (competências) da página e as retorna como um item.
        """
        # Salva o HTML para debugging, se necessário.
        # with open("debug_response.html", "wb") as f:
        #     f.write(response.body)
        # self.logger.info(f"HTML de resposta salvo em: {os.path.abspath('debug_response.html')}")

        datas_disponiveis = response.css('select[name="j_idt76"] option::attr(value)').getall()

        if not datas_disponiveis:
            self.logger.warning("Nenhuma data (competência) encontrada com o seletor 'select[name=\"j_idt76\"]'.")
            return

        # O yield é a forma padrão do Scrapy de "retornar" um item.
        # A API irá capturar este item através do sinal 'item_scraped'.
        yield {"datas_disponiveis": datas_disponiveis}
