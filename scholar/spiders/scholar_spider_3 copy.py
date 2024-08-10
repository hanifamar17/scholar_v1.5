import scrapy
import json
from scrapy.spiders import CrawlSpider
from urllib.parse import urlencode


class ScholarSpider(CrawlSpider):
    name = ""
    api_key = "264149b9f24331932b46064ea1c49d13703be61e3db66273505fb177b18e83c7"
    found_titles = set()

    custom_settings = {
        "DOWNLOAD_DELAY": 2,  # Atur keterlambatan unduhan untuk menghindari kecepatan tinggi
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        'ITEM_PIPELINES':{
            "scholar.pipelines.ScholarCrawlingPipeline":1,
            "scholar.pipelines.MysqlPipeline": 2
        }
    }
    
    def start_requests(self):
        query_keyword = getattr(self, 'query_keyword', None)
        query_institusi = "uin sunan kalijaga"
        
        print(f"Start Requests: Query Keyword - {query_keyword}")

        if query_keyword:
            queries = query_keyword.split(',')
        else:
            queries = ['']
        
        for query in queries:
            url = f'https://serpapi.com/search.json?{urlencode({"engine": "google_scholar_profiles", "mauthors": query.strip() +" "+ query_institusi, "api_key": self.api_key})}'
            yield scrapy.Request(url, callback=self.parse, meta={'query': query.strip()})
            
    def parse(self, response):
        print(f"Parse: Processing URL - {response.url}")
        query = response.meta.get('query')

        data = json.loads(response.text)
        if 'profiles' in data:
            for profile in data['profiles']:
                if 'author_id' in profile:
                    author_id = profile['author_id']
                    author_url = f'https://serpapi.com/search.json?author_id={author_id}&engine=google_scholar_author&hl=en&num=100&api_key={self.api_key}'
                    yield scrapy.Request(author_url, callback=self.parse_author, meta={'query': query})
    
    def parse_author(self, response):
        print(f"Parse: Processing profile_link - {response.url}")
        query = response.meta.get('query')

        data = json.loads(response.text)
        if 'author' in data:
            author = data['author']
            self.thumbnail=author.get('thumbnail', '-')
            

        if 'articles' in data:
            articles = data['articles']
            
            for article in articles:
                title=article.get('title', '-')
                if title in self.found_titles:
                    continue

                self.found_titles.add(title)

                item = {
                    "query": query,
                    "author": article.get('authors', '-'),
                    "title": title,
                    "title_url": article.get('link', '-'),
                    "cited_by_value": article['cited_by'].get('value', '0') if 'cited_by' in article else '-',
                    "cited_by_url": article['cited_by'].get('link', '-') if 'cited_by' in article else '-',
                    "publication_year": article.get('year', '0'),
                    "thumbnail": self.thumbnail
                }
                yield item
        
        #if 'serpapi_pagination' in data:
         #   next_page = data['serpapi_pagination'].get('next')
          #  if next_page:
           #     yield scrapy.Request(next_page, callback=self.parse_author)
    
   # rules = (
    #    Rule(LinkExtractor(allow=('/citations\?user=\w+&hl=en&oi=ao',)), callback='parse_profile'),
    #)
 
  
    
