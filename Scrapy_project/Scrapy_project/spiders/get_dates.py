import scrapy

class DateFinderSpider(scrapy.Spider):
    """
    Spider base que encontra as datas (competências) disponíveis no SISAB.
    Quando executado diretamente (`scrapy crawl date_finder`), retorna as datas encontradas.
    Quando herdado, passa as datas para o método `process_dates` do spider filho.
    """
    name = "date_finder"

    def start_requests(self):
        """
        Faz o primeiro GET para a página do SISAB.
        """
        url = "https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        yield scrapy.Request(url=url, callback=self.parse_page)

    def parse_page(self, response):
        """
        Extrai as datas e as passa para o método de processamento.
        """
        datas_disponiveis = response.css('select[name="j_idt76"] option::attr(value)').getall()

        if not datas_disponiveis:
            self.logger.warning("Nenhuma data (competência) encontrada.")
            return

        # O `yield from` permite que o método do spider filho (se existir) retorne suas próprias requisições.
        yield from self.process_dates(response, datas_disponiveis)

    def process_dates(self, response, dates):
        """
        Método padrão para processar as datas. Spiders filhos devem sobrescrevê-lo.
        Se este spider for executado diretamente, ele simplesmente retorna as datas.
        """
        self.logger.info(f"Spider base encontrou {len(dates)} datas.")
        yield {
            "datas_disponiveis": dates
        }
