import scrapy
import os
from random import randint
from .get_dates import DateFinderSpider


class SisabSpider(DateFinderSpider):
    datas_alvo = ["202502" ,"202501", "202412", "202411", "202410", "202409", "202408", "202407", "202406", "202405", "202404",
                  "202403"]

    name = "sisab"

    def dates_filter(self, datas_alvo: list[str], datas_disponiveis: list[str]):
        """
        Filtra as datas requeridas com base nas datas disponíveis.
        """

        datas_filtradas = []
        for data in datas_disponiveis:
            if data in datas_alvo:
                datas_filtradas.append(data)
        return datas_filtradas


    def process_dates(self, response, dates):
        """
        Extrai o javax.faces.ViewState e monta o POST final
        """

        viewstate = response.css('input[name="javax.faces.ViewState"]::attr(value)').get()
        if not viewstate:
            self.logger.error("ViewState não encontrado!")
            return

        self.logger.info(f"ViewState capturado: {viewstate[:25]}...")

        # Filtragem das datas
        datas_para_usar = self.dates_filter(self.datas_alvo, dates)

        form_data = {
            "j_idt44": "j_idt44",
            "lsCid": "",
            "dtBasicExample_length": "10",
            "lsSigtap": "",
            "td-ls-sigtap_length": "10",
            "unidGeo": "estado",

            # Seleção de estados
            "estados": [
                "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
                "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"
            ],

            # Periodo de datas
            "j_idt76": datas_para_usar,

            "selectLinha": "ATD.CO_UF_IBGE",
            "selectcoluna": "CO_TIPO_ATENDIMENTO",

            # Tipos de equipe
            "j_idt89": ["eq-esf","eq-eacs","eq-nasf","eq-eab","eq-ecr","eq-sb","eq-epen","eq-eap"],

            # Categorias dos profissionais
            "categoriaProfissional": [
                "3","5","6","7","8","9","10","11","12","13","14","15","16","17",
                "18","19","20","21","22","23","24","25","26","27","30","31"
            ],

            "idadeInicio": "0",
            "idadeFim": "0",

            # Locais de atendimento
            "localAtendimento": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],

            # Tipos de atendimento
            "tipoAtendimento": ["2", "5", "6"],

            # Tipos de produção
            "tpProducao": "4",

            # Condição avaliada
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

        output_dir = os.path.join(os.path.expanduser('~'), "Downloads")
        os.makedirs(output_dir, exist_ok=True)

        file_id = randint(1, 10000)
        filename = f"Relatório-SISAB_{file_id}.csv"
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
