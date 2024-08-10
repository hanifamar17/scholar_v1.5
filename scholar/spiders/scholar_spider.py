import scrapy
from scrapy.spiders import CrawlSpider
from urllib.parse import urlencode
from cssselect import Selector
from lxml import etree


custom_settings = {
        "DOWNLOAD_DELAY": 2,  # Atur keterlambatan unduhan untuk menghindari kecepatan tinggi
}

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}  

PROXY_MODE = 0

class ScholarSpider(CrawlSpider):
    name = "dataCrawler"
    allowed_domains = ["scholar.google.com"]
    #start_urls = ['https://scholar.google.com/scholar']
    

    def start_requests(self):
        #querys=['intitle:"UIN Sunan Kalijaga"', 'inauthor:"Agus mulyanto"']
        #query_keyword = ["agung fatwanto uin sunan kalijaga"]
        #author_query = ["mandahadi"]
        #institution_query = ["uin sunan kalijaga".lower().split()]
   
        # Mendapatkan nilai query_keyword dari attribute spider
        query_keyword = getattr(self, 'query_keyword', None)
        #author_query = getattr(self, 'author_query', None)
        #institution_query = getattr(self, 'institution_query', None)
        print(f"Start Requests: Query Keyword - {query_keyword}")
        #print(f"Author query: {author_query}")
        #print(f"Institution query: {institution_query}")

        if query_keyword:
            queries = [query_keyword]
        else:
            queries = ['']
        
        for query in queries:
            url = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&{urlencode({"q": query})}'
            yield scrapy.Request(url, callback=self.parse)
            
    def parse(self, response):
        print(f"Parse: Processing URL - {response.url}")

        #author_query = response.meta.get('author_query')
        #print(f"Author query: {author_query}")
        
        max_pages = 10  # Jumlah halaman yang ingin dicrawling
        crawled_pages = getattr(self, 'crawled_pages', 0)

        # Mendapatkan tautan ke halaman berikutnya
        next_page = response.css('#gs_nml .gs_nma[href*=start]::attr(href)').get()

        # Jika tautan ke halaman berikutnya tersedia dan jumlah halaman yang telah di-crawl belum mencapai batas
        if next_page and crawled_pages < max_pages:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

        # Memperbarui jumlah halaman yang telah di-crawl
        self.crawled_pages = crawled_pages + 1

        for result in response.css("div.gs_ri"):
            #author = result.css('.gs_a a:contains("{author_query}")::text').get(default='')

            item = {
                "author": result.css('div.gs_a a b::text').get(default='-'),
                #"author": author.strip() if author else '',
                "title": result.css("h3 a::text").get(default='-'),
                "publication_year": result.css("div.gs_a::text").re_first(r"\b(\d{4})\b", default='-'),
                #"institutions" : result.css("div.gs_rs::text").get(default=''),
                "link": result.css("h3 a::attr(href)").get(default='-'),
            }
            yield item
        
        
            #yield scrapy.Request(url=next_page, callback=self.parse, headers=headers, dont_filter=True, meta={'dont_retry': True})
 
  
    
