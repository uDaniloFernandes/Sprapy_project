import scrapy
import os
from random import randint

class SisabSpider(scrapy.Spider):
    name = "sisab"

    def start_requests(self):
        url = "https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        yield scrapy.Request(url=url, headers=headers, callback=self.parse_viewstate)

    def parse_viewstate(self, response):
        viewstate = response.css('input[name="javax.faces.ViewState"]::attr(value)').get()
        if not viewstate:
            self.logger.error("ViewState não encontrado!")
            return

        self.logger.info(f"ViewState capturado: {viewstate[:20]}...")

        # Monta os filtros do relatório
        form_data = {
            "j_idt44": "j_idt44",
            "lsCid": "",
            "dtBasicExample_length": "10",
            "lsSigtap": "",
            "td-ls-sigtap_length": "10",
            "unidGeo": "brasil",   # pode trocar para 'municipio'
            "j_idt76": "202508",   # competência (ano/mês)
            "selectLinha": "BRASIL",
            "selectcoluna": "CO_TIPO_FICHA_ATENDIMENTO",
            "idadeInicio": "0",
            "idadeFim": "0",
            "tpProducao": "",
            "javax.faces.ViewState": viewstate,
            "j_idt192": "j_idt192"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://sisab.saude.gov.br",
            "Referer": response.url,
            "User-Agent": "Mozilla/5.0"
        }

        # Faz o POST que retorna o CSV direto
        yield scrapy.FormRequest(
            url=response.url,
            formdata=form_data,
            method="POST",
            headers=headers,
            callback=self.save_csv
        )

    def save_csv(self, response):
        """
        Salva o aqruivo .csv no diretorio especifico
        """
        output_dir = r"C:\Users\CintraMan\Downloads"
        os.makedirs(output_dir, exist_ok=True)

        file_id = randint(1, 10000)
        filename = f"Relatorio-SISAB_{file_id}.csv"
        path = os.path.join(output_dir, filename)

        with open(path, "wb") as f:
            f.write(response.body)

        self.logger.info(f"CSV salvo com sucesso: {path}")
