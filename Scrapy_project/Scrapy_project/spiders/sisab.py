import scrapy
import os
from random import randint
from .get_dates import DateFinderSpider


class SisabSpider(DateFinderSpider):
    datas_alvo = ["202502" ,"202501", "202412", "202411", "202410", "202409", "202408", "202407", "202406", "202405", "202404",
                  "202403"]

    name = "sisab"

    # Este método é a "ponte" entre a API e o Spider.
    def start_requests(self):
        """
        Captura o `task_id` passado pela linha de comando (`-a task_id=...`)
        e o injeta na requisição inicial para que ele seja rastreado.
        """
        # Pega o 'task_id' passado via argumento. Se não houver, o spider funcionará normalmente, mas sem a lógica da API.
        task_id = getattr(self, 'task_id', None)
        
        # Chama o start_requests original do DateFinderSpider (que busca a página),
        # mas agora passando o task_id no meta da requisição.
        for req in super().start_requests():
            if task_id:
                req.meta['task_id'] = task_id
            yield req

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
        # Passa o task_id para a próxima requisição
        task_id = response.meta.get('task_id')

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
            meta={'task_id': task_id} # Garante que o task_id chegue na função final
        )


    def save_csv(self, response):
        """
        Salva o arquivo CSV retornado pelo POST, com lógica de erro robusta.
        """
        # Para integração com a API, um 'task_id' pode ser passado via meta.
        # Se não houver, usa um número aleatório para manter a compatibilidade.
        task_id = response.meta.get('task_id', f"random_{randint(1, 10000)}")

        try:
            # Validação da Resposta: Garante que o servidor não retornou uma página de erro.
            content_type = response.headers.get("Content-Type", b"").decode()
            if "csv" not in content_type and "octet-stream" not in content_type:
                # Este é um erro de lógica de negócio, não de sistema.
                # A requisição foi feita com parâmetros que o servidor não aceitou.
                raise IOError(f"O servidor retornou um tipo de conteúdo inesperado ({content_type}) em vez de um arquivo CSV. A requisição pode ter sido inválida.")

            # Definição do Caminho de Saída Dinâmico
            # Para o deploy, lê o caminho do disco a partir de uma variável de ambiente.
            # Para testes locais, continua usando a pasta Downloads como padrão.
            output_dir = os.environ.get("RENDER_DISK_PATH", os.path.join(os.path.expanduser('~'), "Downloads"))
            os.makedirs(output_dir, exist_ok=True)
            filename = f"Relatorio-SISAB_{task_id}.csv"
            path = os.path.join(output_dir, filename)

            # Escrita do Arquivo
            with open(path, "wb") as f:
                f.write(response.body)

            self.logger.info(f"CSV da tarefa '{task_id}' salvo com sucesso em: {path}")
            # Em um fluxo de API, aqui você atualizaria o status da tarefa para "CONCLUIDO"
            # db_client.update_task(task_id=task_id, status="CONCLUIDO")

        except Exception as e:
            # Captura Centralizada de Erros na Função
            error_message = f"Falha ao processar e salvar o resultado da tarefa '{task_id}': {e}"
            self.logger.error(error_message)
            # Em um fluxo de API, aqui você atualizaria o status da tarefa para "ERRO"
            # db_client.update_task(task_id=task_id, status="ERRO", error_message=str(e))
