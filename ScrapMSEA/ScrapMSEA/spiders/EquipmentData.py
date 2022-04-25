from tokenize import Triple
from urllib.request import Request
import weakref
from requests import request
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import re
import pandas


EquipmentURLS = [
    "http://maplestory.fandom.com/wiki/Category:Secondary_Weapons",
        "http://maplestory.fandom.com/wiki/Category:Equipment_Sets",
        "http://maplestory.fandom.com/wiki/Sealed_Genesis_Weapon_Box",
        "http://maplestory.fandom.com/wiki/Category:Superior_Equipment",
        "http://maplestory.fandom.com/wiki/Android_Heart"
]
EquipSetTrack = [
    'Sengoku', 'Boss Accessory', 'Pitched Boss', 'Seven Days', "Ifia's Treasure",'Mystic','Ardentmill','Blazing Sun'
    ,'8th', 'Root Abyss','AbsoLab', 'Arcane'
    ,'Lionheart', 'Dragon Tail','Falcon Wing','Raven Horn','Shark Tooth'
    ,'Gold Parts','Pure Gold Parts'
    ]
WeapSetTrack = [
    'Utgard', 'Lapis','Lazuli'
    ,'Fafnir','AbsoLab', 'Arcane', 'Genesis'
    ]

class WeapondataSpider(scrapy.Spider):
    name = 'EquipmentData'
    allowed_domains = ['maplestory.fandom.com']
    start_urls = ["http://maplestory.fandom.com/wiki/Category:Weapons"]
    custom_settings = {"FEEDS":{"results.csv":{"format":"csv"}}}

    DictKeys = []
    WeapDict = pandas.DataFrame()

    def parse(self, response):
        #for href in response.xpath('//li[@class="category-page__member"]/a/@href').extract():
        request = []
        for href in response.css('a.category-page__member-link::attr(href)'):
            wtype = " ".join(re.split('_|-' , href.extract().split(':')[-1])).strip(' ')
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.WeaponType, meta = {"WeaponType" : wtype})
            ...
        
        print(request)
        
    
    def WeaponType(self, response):
        ItemDict = {}
        ItemDict["WeaponType"] = response.meta.get('WeaponType')
        for href in response.css('a.category-page__member-link::attr(href)'):
            hrefcat = re.split('/|_|%', href.extract())
            match = False
            for wtrack in WeapSetTrack:
                if wtrack in hrefcat:
                    ItemDict["Set"] = wtrack
                    match = True
            if match:
                url = response.urljoin(href.extract())
                yield scrapy.Request(url, callback=self.IndividualWeapon, cb_kwargs= {'item' : ItemDict})
        
        
    
    def IndividualWeapon(self, response, item):
        tables = response.css('div.mw-parser-output > table > tbody > tr')

        for row in tables:
            th = row.xpath('th//text()').getall()
            td = row.xpath('td//text()').getall()
            if "Tradability\n" in th:
                break
            if th != []:
                key = th[0].strip('\n ')
                if key not in self.DictKeys:
                    self.DictKeys.append(key)
                value = "|".join(td).strip("|\n+%")
                item[key] = value
        
        for keys in self.DictKeys:
            if keys not in item.keys():
                item[keys] = 0
        
        self.WeapDict = self.WeapDict.append(pandas.DataFrame(item, index=[0]), ignore_index=True)
        
        return item 
        
                            



#process = CrawlerProcess(get_project_settings())
#process.crawl(WeapondataSpider)
#process.start()
