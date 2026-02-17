# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobFinderItem(scrapy.Item):
    keyword_searched = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    type = scrapy.Field()
    link = scrapy.Field()
    source = scrapy.Field()
    budget = scrapy.Field()
    salary = scrapy.Field()
    date_posted = scrapy.Field()
    description = scrapy.Field()
