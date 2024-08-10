# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import mysql.connector
import re


class DosenCrawlingPipeline:
    def __init__(self):
        self.file = open('output_dosen.json','w')
        self.title_pattern = re.compile(r',?\s*(S\.Si\.|S\.Kom\.|M\.Kom\.|Dr\.|Ir\.|S\.T\.|M\.T\.||M\.Eng\.|M\.Cs)')
    
    def process_item(self, item, spider):
        cleaned_name = self.title_pattern.sub('', item['nama']).strip()

        data = {
        "id_dosen": item['id_dosen'],
        "nama": cleaned_name,   
        "institusi": item['institusi'],
        }
        return item
    
    def close_spider(self, spider):
        self.file.close()

class ProfilesCrawlingPipeline:
    def __init__(self):
        self.file = open('output_profiles.json','w')
    
    def process_item(self, item_profiles, spider):
        item_profiles = {
        "name": item_profiles['name'],
        "affiliations": item_profiles['affiliations'],
        "thumbnail": item_profiles['thumbnail'],
        "author_id": item_profiles['author_id'],
        "interests": item_profiles['interests']
        }

        return item_profiles
    
    def close_spider(self, spider):
        self.file.close()

class ScholarCrawlingPipeline:
    def __init__(self):
        self.file = open('output.json','w')
        
    
    def process_item(self, item, spider):
        #if 'title' in item and isinstance(item['title'], list):
         #   item['title'] = ', '.join(item['title'])
            
        item = {
        "query": item['query'],
        "author": item['author'],
        "title": item['title'],
        "title_url": item['title_url'],
        "cited_by_value": item['cited_by_value'],
        "cited_by_url": item['cited_by_url'],
        "publication_year": item['publication_year'],
        "thumbnail": item['thumbnail']
        }

        return item
    
    def close_spider(self, spider):
        self.file.close()


class MysqlPipeline:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '',
            database = 'crawlings'
        )

        ## Create cursor, used to execute commands
        self.cur = self.conn.cursor()
   
    def process_item(self, item, spider):
        ## Check to see if text is already in database 
        self.cur.execute("SELECT * FROM publikasi where title = %s", (item['title'],))
        result = self.cur.fetchone()

        if result:
            spider.logger.warning("Item already in database: %s" % (item['title'],))
        else:
            publication_year = item['publication_year']
            if not publication_year or not publication_year.isdigit():
                publication_year = None

            self.cur.execute(""" INSERT INTO publikasi (query, author, title, title_url, cited_by_value, cited_by_url, publication_year, thumbnail, created_at, updated_at) 
                             values (%s,%s,%s,%s,%s,%s,%s,%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""", 
            (
                item["query"],
                item["author"],
                item['title'],
                item["title_url"],
                item["cited_by_value"],
                item["cited_by_url"],
                publication_year,
                item["thumbnail"]
            ))

            ## Execute insert of data into database
            self.conn.commit()
            spider.logger.info(f"Item inserted into database: {(item['title'],)}")
        return item
        
    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

class MysqlDosenPipeline:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '',
            database = 'crawlings'
        )

        ## Create cursor, used to execute commands
        self.cur = self.conn.cursor()
   
    def process_item(self, item, spider):
        
        ## Check to see if text is already in database 
        self.cur.execute("SELECT * FROM dosen where nama = %s", (item['nama'],))
        result = self.cur.fetchone()

        if result:
            spider.logger.warning("Item already in database: %s" % item['nama'])
        else:
            self.cur.execute(""" INSERT INTO dosen (nama, prodi, created_at, updated_at) 
                             values (%s,%s,%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""", 
            (
                item["nama"],
                item["prodi"]
            ))

            ## Execute insert of data into database
            self.conn.commit()
            spider.logger.info(f"Item inserted into database: {item['nama']}")
        return item
        
    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
