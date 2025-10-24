import scrapy

class DateFinderSpider(scrapy.Spider):
    name = "date_finder"
    
    # Adicionamos uma lista de classe para coletar os itens que o spider produz.
    # A API irá ler desta lista após a execução do spider.
    items = []

    def __init__(self, *args, **kwargs):
        """
        O construtor é chamado toda vez que o spider é iniciado.
        Limpamos a lista de itens para garantir que cada execução seja isolada.
        """
        super().__init__(*args, **kwargs)
        self.items.clear()

    def start_requests(self):
        """
        Faz o primeiro GET para a página de relatórios.
        """
        url = "https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        yield scrapy.Request(url=url, callback=self.parse_dates)

    def parse_dates(self, response):
        """
        Extrai as datas disponíveis (competências) da página.
        """
        datas_disponiveis = response.css('select[name="j_idt76"] option::attr(value)').getall()

        if not datas_disponiveis:
            self.logger.warning("Nenhuma data (competência) encontrada.")
            return

        item = {"datas_disponiveis": datas_disponiveis}
        
        # Adiciona o item à lista da classe para que a API possa acessá-lo
        self.items.append(item)
        
        # O yield ainda é importante para o fluxo padrão do Scrapy
        yield item
