import scrapy


class GamesTopPlaying(scrapy.Spider):
    name = "game_top_playing"

    def start_requests(self):
        url = 'https://howlongtobeat.com/stats'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
        yield scrapy.Request(url, headers=headers)


    def parse(self, response):

        pass

# fetch('https://howlongtobeat.com/stats', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'})