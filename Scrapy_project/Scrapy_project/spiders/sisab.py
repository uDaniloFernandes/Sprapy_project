import scrapy

class SisabSpider(scrapy.Spider):
    name = "spider-sisab"

    def __init__(self, datas_alvo=None, output_file=None, *args, **kwargs):
        """
        Este método é chamado quando o spider é iniciado pela API.
        - datas_alvo: A lista de datas escolhida pelo usuário.
        - output_file: O caminho do arquivo onde o CSV deve ser salvo.
        """
        super().__init__(*args, **kwargs)
        self.datas_alvo = datas_alvo or []
        self.output_file = output_file

        if not self.datas_alvo:
            self.logger.error("Spider SisabSpider iniciado sem o parâmetro 'datas_alvo'.")
        if not self.output_file:
            self.logger.error("Spider SisabSpider iniciado sem o parâmetro 'output_file'.")


    def start_requests(self):
        """
        Faz o primeiro GET para a página de relatórios para capturar o ViewState.
        """
        url = "https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        yield scrapy.Request(url=url, callback=self.parse_and_submit)


    def parse_and_submit(self, response):
        """
        Extrai o javax.faces.ViewState e monta o POST final.
        """
        viewstate = response.css('input[name="javax.faces.ViewState"]::attr(value)').get()
        if not viewstate:
            self.logger.error("ViewState não encontrado!")
            return

        self.logger.info(f"ViewState capturado: {viewstate[:25]}...")

        # As datas a usar vêm diretamente do parâmetro 'datas_alvo' recebido.
        datas_para_usar = self.datas_alvo
        if not datas_para_usar:
            self.logger.error("Nenhuma data foi fornecida para a extração.")
            return

        form_data = {
            "j_idt44": "j_idt44",
            "lsCid": "",
            "dtBasicExample_length": "10",
            "lsSigtap": "",
            "td-ls-sigtap_length": "10",

            # Unidade Geografica
            "unidGeo": "estado",

            # Unidades Federativas
            "estados": [
                "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
                "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"
            ],

            # Periodo de Datas
            "j_idt76": datas_para_usar,

            # Linha da Tabela
            "selectLinha": "ATD.CO_UF_IBGE",

            # Coluna da Tabela
            "selectcoluna": "CO_TIPO_ATENDIMENTO",

            # Equipes de Atendimento
            "j_idt89": ["eq-esf","eq-eacs","eq-nasf","eq-eab","eq-ecr","eq-sb","eq-epen","eq-eap"],

            # Categorias de Profissional
            "categoriaProfissional": [
                "3","5","6","7","8","9","10","11","12","13","14","15","16","17",
                "18","19","20","21","22","23","24","25","26","27","30","31"
            ],
            "idadeInicio": "0",
            "idadeFim": "0",

            # Locais de Atendimento
            "localAtendimento": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],

            # Tipo de Atendimento
            "tipoAtendimento": ["2", "5", "6"],

            # Tipo de Produção
            "tpProducao": "4",

            # Condição de Avaliação
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
        Salva o arquivo CSV retornado pelo POST diretamente no caminho fornecido pela API.
        """
        try:
            # Validação da Resposta
            content_type = response.headers.get("Content-Type", b"").decode()
            if "csv" not in content_type and "octet-stream" not in content_type:
                raise IOError(f"O servidor retornou um tipo de conteúdo inesperado ({content_type}) em vez de um arquivo CSV.")

            if not self.output_file:
                raise ValueError("O caminho do arquivo de saída (output_file) não foi fornecido ao spider.")

            # Escrita do Arquivo no caminho temporário fornecido pela API
            with open(self.output_file, "wb") as f:
                f.write(response.body)

            self.logger.info(f"CSV salvo com sucesso em: {self.output_file}")

        except Exception as e:
            self.logger.error(f"Falha ao salvar o resultado da extração: {e}")
            # Levanta a exceção novamente para que o CrawlerProcess da API saiba que a extração falhou.
            raise
