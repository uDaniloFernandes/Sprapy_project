import scrapy


class ImdbSpider(scrapy.Spider):
    name = "imdb"

    def start_requests(self):
        url = 'https://www.imdb.com/chart/top/?ref_=chttp_ql_3'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
        yield scrapy.Request(url, headers=headers)


    def parse(self, response):
        list_film = []
        for filme in response.css('.cli-children'):
            titulo = filme.css('.with-margin .ipc-title__text--reduced::text').get()
            rank, nome = titulo.split('.', 1)

            ano = filme.css('.cli-title-metadata-item:nth-child(1)::text').get()

            duracao = filme.css('.cli-title-metadata-item:nth-child(2)::text').get()

            f_etaria = filme.css('.cli-title-metadata-item~ .cli-title-metadata-item+ .cli-title-metadata-item::text').get()

            nota = filme.css('span.ipc-rating-star--rating::text').get()

            film = [rank, nome[1::], ano, duracao, f_etaria, nota]
            list_film.append(film)

        print('======================= resultado =======================')
        print(list_film)
        pass



"""
Nome: .with-margin .ipc-title__text--reduced::text
Ano: .cli-title-metadata-item:nth-child(1)::text
Duração: .cli-title-metadata-item:nth-child(2)::text
Classificação etaria: .cli-title-metadata-item~ .cli-title-metadata-item+ .cli-title-metadata-item::text
Avaliação: .cli-ratings-container::text

(::text) para acessar apenas o texto

scrapy crawl imdb
"""


# fetch('https://www.imdb.com/pt/chart/top/', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'})