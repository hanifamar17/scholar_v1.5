import scrapy
import json
from scrapy.spiders import CrawlSpider
from urllib.parse import urlencode


class ProfilesSpider(CrawlSpider):
    name = "dataCrawler_4"
    api_key = "4b387964df59b8dbbbc23acd0798bde5e774217ad903179082a931ecd5a5f92e"
    #api_key = "fdNqwpIHSbCdDq9wdBMcbhOyaDkTRfVq"
    base_url = "https://serpapi.webscrapingapi.com/v1"
    engine = "google_scholar_profiles"

    custom_settings = {
        "DOWNLOAD_DELAY": 2,  # Atur keterlambatan unduhan untuk menghindari kecepatan tinggi
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        'FEED_URI': 'output_profiles.json',
        'FEED_FORMAT': 'json',
        'ITEM_PIPELINES':{
            "scholar.pipelines.ProfilesCrawlingPipeline":1,
        }
    }
    
    def start_requests(self):
        query_keyword = getattr(self, 'query_keyword', '-')
        query_institusi = "uin sunan kalijaga"
        #query_keyword="shofwatul"
        print(f"Start Requests: Query Keyword - {query_keyword}")

        if query_keyword is None:
            self.logger.warning("query is None. Stopping Scrapy.")
            return
        
        queries = query_keyword.split(',')
        
        for query in queries:
            url = f'https://serpapi.com/search.json?{urlencode({"engine": "google_scholar_profiles", "mauthors": query.strip() +" "+ query_institusi, "api_key": self.api_key})}'
            #url = f"{self.base_url}?api_key={self.api_key}&engine={self.engine}&mauthors={query.strip()} {query_institusi}"
            yield scrapy.Request(url, callback=self.parse_profiles, meta={'query': query.strip()})
            
    def parse_profiles(self, response):
        print(f"Parse: Processing URL - {response.url}")
        query = response.meta.get('query')

        data = json.loads(response.text)
        if 'profiles' in data:
            for profile in data['profiles']:

                interests = []
                if 'interests' in profile:
                    for interest in profile['interests']:
                        interests.append(interest.get('title', '-'))

                item_profile = {
                    "name": profile.get('name', '-'),
                    "affiliations": profile.get('affiliations', '-'),
                    "thumbnail": profile.get('thumbnail', '-'),
                    "author_id": profile.get('author_id', '-'),
                    "interests": interests
                }
                yield item_profile
    
    
 
  
    
