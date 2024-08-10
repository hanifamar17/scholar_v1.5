import scrapy
from scrapy.spiders import CrawlSpider
from urllib.parse import urlencode


class DosenSpider(CrawlSpider):
    name = "dosenCrawler"
    allowed_domains = ["informatika.uin-suka.ac.id"]
    start_urls = ["https://informatika.uin-suka.ac.id/id/page/dosen"]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,  # Atur keterlambatan unduhan untuk menghindari kecepatan tinggi
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        'FEED_URI': 'output_dosen.json',
        'FEED_FORMAT': 'json',
        'ITEM_PIPELINES':{
            "scholar.pipelines.DosenCrawlingPipeline":1,
            #"scholar.pipelines.MysqlDosenPipeline":2
        }
    }
    def start_requests(self):
        urls=["https://informatika.uin-suka.ac.id/id/page/dosen"]

        for url in urls:
            self.logger.info(f'Fetching URL: {url}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
       dosen_list = response.css('div.main div.container div.row div.col-md-9 div.article-content table.table tbody tr')

       for dosen in dosen_list:
            id_dosen = dosen.css('td a u::text').get().strip()
            nama = dosen.css('td[style="text-indent: 10px;"]::text').get().strip()

            item = {
                "id_dosen":id_dosen,
                "nama": nama,
                "institusi":"UIN Sunan Kalijaga"
            }
            yield item
 
  
    
