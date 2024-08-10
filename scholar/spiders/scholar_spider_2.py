import scrapy
from scrapy.spiders import CrawlSpider
from urllib.parse import urlencode


custom_settings = {
        "DOWNLOAD_DELAY": 2,  # Atur keterlambatan unduhan untuk menghindari kecepatan tinggi
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

PROXY_MODE = 0

class ScholarSpider(CrawlSpider):
    name = "dataCrawler_2"
    allowed_domains = ["scholar.google.com"]
    found_titles = set()
    
    def start_requests(self):
        #query_keyword = ["agus mulyanto uin sunan kalijaga"]
        query_keyword = getattr(self, 'query_keyword', None)
        query_institusi = "uin sunan kalijaga"
        print(f"Start Requests: Query Keyword - {query_keyword}")

        if query_keyword:
            queries = query_keyword.split(';')
        else:
            queries = ['']
        
        for query in queries:
            url = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&{urlencode({"q": query.strip() +" "+ query_institusi})}'
            yield scrapy.Request(url, callback=self.parse,  meta={'query': query.strip()})
            
    def parse(self, response):
        print(f"Parse: Processing URL - {response.url}")
        query = response.meta.get('query')

        for author_link in response.css('#gs_res_ccl_mid .gs_r h4.gs_rt2 a::attr(href)').getall():
            author_url = response.urljoin(author_link)
            yield scrapy.Request(author_url, callback=self.parse_author, meta={'query': query})

        #show_more_button = response.css('button#gsc_bpf_more')
        #if show_more_button and not show_more_button.attrib.get('[disabled]'):
         #   self.start += 10
          #  next_page_url = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&{urlencode({"q": self.query})}&start=10'
           # yield scrapy.Request(next_page_url, self.parse, meta={'query': query})
    
    def parse_author(self, response):
        query = response.meta.get('query')
        author = response.css('div#gsc_prf_in::text').get(default='-')
        articles = response.css('tr.gsc_a_tr')

        for result in articles:
            title = result.css('a.gsc_a_at::text').get(default='-'),
            url = result.css('a.gsc_a_at::attr(href)').get()
            url = response.urljoin(url)
            cited_by_value = result.css('td.gsc_a_c a.gsc_a_ac.gs_ibl::text').get()
            cited_by_url = result.css('td.gsc_a_c a.gsc_a_ac.gs_ibl::attr(href)').get()
            cited_by_url = response.urljoin(cited_by_url)

            if title in self.found_titles:
                continue

            self.found_titles.add(title)

            item = {
                "query": query,
                "author": author,
                "title": title,
                "title_url":url,
                "cited_by_value": cited_by_value,
                "cited_by_url": cited_by_url,
                "publication_year": result.css('span.gsc_a_h::text').re_first(r"\b(\d{4})\b", default='-'),
            }
            yield item
 
  
    
