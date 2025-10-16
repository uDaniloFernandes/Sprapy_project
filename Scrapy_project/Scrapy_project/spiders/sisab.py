import scrapy
import os
from random import randint


class SisabSpider(scrapy.Spider):
    datas_alvo = ["202502" ,"202501", "202412", "202411", "202410", "202409", "202408", "202407", "202406", "202405", "202404",
                  "202403"]

    name = "sisab"

    def start_requests(self):
        """
        Faz o primeiro GET para capturar o ViewState
        """

        url = "https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        yield scrapy.Request(url=url, callback=self.parse_viewstate)


    def get_all_dates(self, response):
        """
        Extrai todos os valores de competência (datas) do elemento <select name="j_idt76"> oculto.
        """

        # Coletando as datas disponiveis:
        datas_disponiveis = response.css('select[name="j_idt76"] option::attr(value)').getall()

        if not datas_disponiveis:
            self.logger.warning("Nenhuma data (competência) encontrada no elemento oculto.")
            return []

        return datas_disponiveis


    def dates_filter(self, datas_alvo: list[str], datas_disponiveis: list[str]):
        datas_filtradas = []
        for data in datas_disponiveis:
            if data in datas_alvo:
                datas_filtradas.append(data)
        return datas_filtradas


    def parse_viewstate(self, response):
        """
        Extrai o javax.faces.ViewState e monta o POST final
        """

        viewstate = response.css('input[name="javax.faces.ViewState"]::attr(value)').get()
        if not viewstate:
            self.logger.error("ViewState não encontrado!")
            return

        self.logger.info(f"ViewState capturado: {viewstate[:25]}...")

        dates = self.dates_filter(self.datas_alvo, self.get_all_dates(response))

        form_data = {
            "j_idt44": "j_idt44",
            "lsCid": "",
            "dtBasicExample_length": "10",
            "lsSigtap": "",
            "td-ls-sigtap_length": "10",
            "unidGeo": "estado",

            # múltiplos estados selecionados
            "estados": [
                "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
                "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"
            ],

            # competências selecionadas
            "j_idt76": dates,

            "selectLinha": "ATD.CO_UF_IBGE",
            "selectcoluna": "CO_TIPO_ATENDIMENTO",

            # tipos de equipe
            "j_idt89": ["eq-esf","eq-eacs","eq-nasf","eq-eab","eq-ecr","eq-sb","eq-epen","eq-eap"],

            # categorias profissionais
            "categoriaProfissional": [
                "3","5","6","7","8","9","10","11","12","13","14","15","16","17",
                "18","19","20","21","22","23","24","25","26","27","30","31"
            ],

            "idadeInicio": "0",
            "idadeFim": "0",

            # locais de atendimento 1 a 10
            "localAtendimento": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],

            "tipoAtendimento": ["2", "5", "6"],
            "tpProducao": "4",
            "condicaoAvaliada": "ABP014",

            "javax.faces.ViewState": viewstate,
            "j_idt192": "j_idt192"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://sisab.saude.gov.br",
            "Referer": response.url,
            "User-Agent": "Mozilla/5.0",
        }

        # Envia o POST que retorna o CSV
        yield scrapy.FormRequest(
            url=response.url,
            formdata=form_data,
            method="POST",
            headers=headers,
            callback=self.save_csv,
        )


    def save_csv(self, response):
        """
        Salva o arquivo CSV retornado pelo POST
        """

        output_dir = r"C:\Users\CintraMan\Downloads"
        os.makedirs(output_dir, exist_ok=True)

        file_id = randint(1, 10000)
        filename = f"Relatorio-SISAB_{file_id}.csv"
        path = os.path.join(output_dir, filename)

        # Garante que a resposta seja CSV
        content_type = response.headers.get("Content-Type", b"").decode()
        if "csv" not in content_type and "octet-stream" not in content_type:
            self.logger.error("O retorno não é CSV/Download. O servidor retornou HTML/Erro.")
            self.logger.debug(f"Tipo de Conteúdo Recebido: {content_type}")
            self.logger.debug(response.text[:500])
            return

        with open(path, "wb") as f:
            f.write(response.body)

        self.logger.info(f"CSV salvo com sucesso em: {path}")


