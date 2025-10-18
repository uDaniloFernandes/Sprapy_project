import scrapy
import os
from datetime import datetime
from typing import List


class DatasusSpider(scrapy.Spider):
    name = "datasus"

    start_urls = ["http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sih/cnv/nibr.def"]

    def get_select_options(self, response: scrapy.http.Response, select_name: str) -> List[str]:
        """Extrai todos os valores (attributes 'value') de um campo <select>."""
        # Seletor genérico para Linha, Coluna, Conteúdo
        selector = f'select[name="{select_name}"] option::attr(value)'
        return response.css(selector).getall()

    def get_period_labels(self, response: scrapy.http.Response) -> List[str]:
        """Extrai os rótulos de Período (que geralmente são os valores a serem enviados)."""
        # Seletor para o campo Período (Arquivos)
        return response.css('select[name="Arquivos"] option::text').getall()

    def parse(self, response):
        """
        Extrai as opções e monta a requisição POST final.
        """
        self.logger.info(f"Página de formulário carregada: {response.url}")

        # 1. Extração de todas as opções
        opcoes_linha = self.get_select_options(response, "Linha")
        opcoes_coluna = self.get_select_options(response, "Coluna")
        opcoes_conteudo = self.get_select_options(response, "Incremento")
        opcoes_periodo_rotulos = self.get_period_labels(response)

        if not opcoes_periodo_rotulos:
            self.logger.error("Nenhuma opção de período (Arquivos) foi encontrada.")
            return


        form_data = {
            # Tenta satisfazer a validação JavaScript:
            "uf": "TO",  # Tenta Brasil como valor padrão se não estiver usando estado
            "mes": "ago",  # Tenta o número do mês (Agosto)
            "ano": "2025",  # Tenta o ano
            "tipo_arquivo": "3",  # Tenta um código para CSV/TXT

            # A chave 'Arquivos[]' provavelmente precisa ser alterada.
            # Use o formato YYYYMM se o servidor esperar isso.
            "Arquivos[]": ["202508"],
        }

        # A URL de ação é a mesma URL da página, pois o formulário POSTa para si mesmo
        yield scrapy.FormRequest(
            url=response.url,
            method="POST",
            formdata=form_data,
            # Headers mínimos (o DATASUS geralmente não exige User-Agent complexo)
            headers={"Referer": response.url},
            callback=self.parse_report
        )

    def parse_report(self, response):
        """
        Processa a resposta, que é o relatório (HTML ou CSV) após o redirecionamento.
        """
        self.logger.info(f"Resposta final (após redirect): {response.url} | Status: {response.status}")

        # 1. Checagem do tipo de conteúdo
        content_type = response.headers.get("Content-Type", b"").decode()

        if "text/csv" in content_type or "octet-stream" in content_type:
            # 2. Lógica de salvamento (se for CSV)
            filename = f"Datasus_Relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            # Salva o arquivo no diretório atual (adapte conforme necessário)
            with open(filename, "wb") as f:
                f.write(response.body)
            self.logger.info(f"Relatório CSV salvo com sucesso: {filename}")

        elif "html" in content_type or response.status == 200:
            # 3. Se retornar HTML, tente raspar a tabela
            self.logger.warning("Retornou HTML. O formulário pode ter falhado na validação.")

            # Aqui você adicionaria a lógica para extrair dados da tabela HTML
            # Ex: tabela = response.css('table.tabnet-table').get()
            # ...

"""
Linha - response.css('select[name="Linha"] option::attr(value)').getall()
Coluna - response.css('select[name="Coluna"] option::attr(value)').getall()
Conteudo - response.css('select[name="Incremento"] option::attr(value)').getall()
Periodo - response.css('select[name="Arquivos"] option::text').getall()
"""