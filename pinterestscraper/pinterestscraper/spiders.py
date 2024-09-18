import json
import os
import cv2
import numpy as np

from scrapy import Spider, Request
from scrapy.http import HtmlResponse
from pydotmap import DotMap

class PinterestSpider(Spider):
    name = 'pinterest'
    allowed_domains = ['www.bing.com', 'www.pinterest.com']
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

    def __init__(self, keyword=None, max_images=None, output_folder='', **kwargs):
        self.keyword = keyword
        self.max_images = max_images
        self.output_folder = output_folder
        self.json_data_list = []
        self.unique_img = []
        super().__init__(**kwargs)

    def start_requests(self):
        yield Request(
            url=f'https://www.bing.com/search?q={self.keyword}%20pinterest&pq={self.keyword}+pinterest&first=1&FORM=PERE',
            callback=self.parse_bing,
            headers={'User-Agent': self.user_agent}
        )

    def parse_bing(self, response):
        # Extract Pinterest links from Bing search results
        pinterest_links = self.get_pinterest_links(response.text, self.max_images)

        # Follow each Pinterest link and parse the page
        for link in pinterest_links:
            yield Request(
                url=link,
                callback=self.parse_pinterest,
                headers={'User-Agent': self.user_agent}
            )

    def parse_pinterest(self, response):
        # Save JSON data from the Pinterest page
        self.get_source(response)

        # Extract image URLs and save them
        url_list = self.save_image_url(self.max_images)

        # Download and save images
        self.download(url_list, self.output_folder)

    # Other methods from your original code...
    # (get_pinterest_links, get_source, save_image_url, dhash, saving_op, download, save_comments)

# Runner script
from scrapy.crawler import CrawlerProcess

if __name__ == '__main__':
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    })
    process.crawl(PinterestSpider, keyword='naruto', max_images=15, output_folder='outputt')
    process.start()