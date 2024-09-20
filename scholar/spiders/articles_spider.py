import scrapy
import json
from scrapy.spiders import CrawlSpider
from urllib.parse import urlencode
import os
from dotenv import load_dotenv
import mysql.connector


class ScholarSpider(CrawlSpider):
    name = "dataCrawler_3"
    
    load_dotenv()  # Memuat variabel dari file .env
    api_key = os.getenv('API_KEY_ARTICLES') #serpapi.com
    found_titles = set()

    custom_settings = {
        "DOWNLOAD_DELAY": 2,  # Atur keterlambatan unduhan untuk menghindari kecepatan tinggi
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        'ITEM_PIPELINES':{
            "scholar.pipelines.ScholarCrawlingPipeline":1,
            #"scholar.pipelines.MysqlPipeline": 2
        }
    }
    
    def start_requests(self):
        author_id = getattr(self, 'author_id', None)
        
        self.logger.info(f"Start Requests: author_id - {author_id}")
        
        if author_id is None:
            self.logger.warning("Author ID is None. Stopping Scrapy.")
            return
        authors = author_id.split(',')

        # Mengambil semua judul dari tabel false_articles sebelum scraping dimulai
        self.load_false_articles()

        for author_id in authors:
            url = f'https://serpapi.com/search.json?author_id={author_id}&engine=google_scholar_author&hl=en&api_key={self.api_key}&num=100' 
            #url = f'https://serpapi.webscrapingapi.com/v1?engine=google_scholar_author&api_key={self.api_key}&author_id={author_id}' 
            yield scrapy.Request(url, callback=self.parse, meta={'author_id': author_id.strip()})
    
    def load_false_articles(self):
        # Buat koneksi ke database MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="publications"
        )
        cursor = conn.cursor()

        # Ambil semua judul dari tabel false_articles
        cursor.execute("SELECT title FROM false_articles")
        results = cursor.fetchall()

        # Simpan semua judul ke dalam set found_titles
        for result in results:
            self.found_titles.add(result[0])

        # Tutup koneksi database
        cursor.close()
        conn.close()

    def parse(self, response):
        print(f"Parse: Processing profile_link - {response.url}")
        author_id = response.meta.get('author_id')

        data = json.loads(response.text)
        if 'author' in data:
            author = data['author']
            self.name = author.get('name', '-')
            self.thumbnail = author.get('thumbnail', '-')
            

        if 'articles' in data:
            articles = data['articles']
            
            for article in articles:
                title=article.get('title', '-')
                if title in self.found_titles:
                    continue
                self.found_titles.add(title)

                item = {
                    "query": self.name,
                    "author": article.get('authors', '-'),
                    "title": title,
                    "title_url": article.get('link', '-'),
                    "cited_by_value": article['cited_by'].get('value', '-') if 'cited_by' in article else '-',
                    "cited_by_url": article['cited_by'].get('link', '-') if 'cited_by' in article else '-',
                    "publication_year": article.get('year', '-'),
                    "publication": article.get('publication', '-'),
                    "thumbnail": self.thumbnail
                }
                yield item

        if 'serpapi_pagination' in data:
            pagination = data['serpapi_pagination']
            next_page_url = pagination.get('next')
            if next_page_url:
                next_page_url_with_key = f"{next_page_url}&api_key={self.api_key}"
                yield scrapy.Request(url=next_page_url_with_key, callback=self.parse, meta={'author_id': author_id.strip()})
  
    
