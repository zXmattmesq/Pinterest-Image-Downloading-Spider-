import json
import os
import cv2
import numpy as np
import random
import requests
from scrapy import Spider, Request
from scrapy.http import HtmlResponse
from bs4 import BeautifulSoup as soup
from pydotmap import DotMap
from concurrent.futures import ThreadPoolExecutor  # Import ThreadPoolExecutor

class PinterestSpider(Spider):
    name = 'pinterest'
    allowed_domains = ['www.bing.com', 'www.pinterest.com']

    def __init__(self, keyword=None, max_images=None, output_folder='', **kwargs):
        self.keyword = keyword
        self.max_images = max_images
        self.output_folder = output_folder
        self.json_data_list = []
        self.unique_img = []
        self.user_agents = self.load_user_agents('valid_user_agents.txt')
        super().__init__(**kwargs)

    @staticmethod
    def load_user_agents(filepath):
        with open(filepath, 'r') as file:
            return [line.strip() for line in file if line.strip()]

    def start_requests(self):
        yield Request(
            url=f'https://www.bing.com/search?q={self.keyword}%20pinterest&pq={self.keyword}+pinterest&first=1&FORM=PERE',
            callback=self.parse_bing,
            headers={'User-Agent': random.choice(self.user_agents)}
        )

    def parse_bing(self, response):
        # Extract Pinterest links from Bing search results
        pinterest_links = self.get_pinterest_links(response.text, self.max_images)

        # Follow each Pinterest link and parse the page
        for link in pinterest_links:
            yield Request(
                url=link,
                callback=self.parse_pinterest,
                headers={'User-Agent': random.choice(self.user_agents)}
                
            )

    def parse_pinterest(self, response):
        # Save JSON data from the Pinterest page
        self.get_source(response)

        # Extract image URLs and save them
        url_list = self.save_image_url(self.max_images)

        # Download and save images
        self.download(url_list, self.output_folder)

    @staticmethod
    def get_pinterest_links(body, max_images: int):
        searched_urls = []
        html = soup(body, 'html.parser')
        links = html.select('#b_results cite')
        for link in links:
            link = link.text
            if "pinterest" in link:
                searched_urls.append(link)
                # stops adding links if the limit has been reached
                if max_images is not None and max_images == len(searched_urls):
                    break
        return searched_urls

    def get_source(self, response: HtmlResponse):
        html = soup(response.text, 'html.parser')
        json_data = html.find_all("script", attrs={"id": "__PWS_INITIAL_PROPS__"})
        self.json_data_list.append(json.loads(json_data[0].string))

    def save_image_url(self, max_images: int) -> list:
        url_list = []
        for js in self.json_data_list:
            try:
                data = DotMap(js)
                urls = []
                for pin in data.initialReduxState.pins:
                    if isinstance(data.initialReduxState.pins[pin].images.get("orig"), list):
                        for i in data.initialReduxState.pins[pin].images.get("orig"):
                            urls.append(i.get("url"))
                    else:
                        urls.append(data.initialReduxState.pins[pin].images.get("orig").get("url"))

                for url in urls:
                    url_list.append(url)
                    if max_images is not None and max_images == len(url_list):
                        return list(set(url_list))
            except Exception:
                continue

        return list(set(url_list))

    def dhash(self, image, hashSize: int = 8):
        resized = cv2.resize(image, (hashSize + 1, hashSize))
        diff = resized[:, 1:] > resized[:, :-1]
        return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

    def saving_op(self, var):
        url_list, folder_name = var
        if not os.path.exists(os.path.join(os.getcwd(), folder_name)):
            os.mkdir(os.path.join(os.getcwd(), folder_name))
        for img in url_list:
            result = requests.get(img, stream=True).content
            file_name = img.split("/")[-1]
            file_path = os.path.join(os.getcwd(), folder_name, file_name)
            img_arr = np.asarray(bytearray(result), dtype="uint8")
            image = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if not self.dhash(image) in self.unique_img:
                cv2.imwrite(file_path, image)
                self.save_comments(image, img, folder_name)  # Save comments for the image
            self.unique_img.append(self.dhash(image))

    def download(self, url_list, output_folder):
        num_of_workers = 10  # You can adjust this based on your needs
        idx = len(url_list) // num_of_workers if len(url_list) > 9 else len(url_list)
        param = []
        for i in range(num_of_workers):
            param.append((url_list[((i * idx)):(idx * (i + 1))], output_folder))
        with ThreadPoolExecutor(max_workers=num_of_workers) as executor:
            executor.map(self.saving_op, param)

    def save_comments(self, image, image_url, folder_name):
        for js in self.json_data_list:
            try:
                data = DotMap(js)
                for pin in data.initialReduxState.pins:
                    if data.initialReduxState.pins[pin].images.get("orig").get("url") == image_url:
                        if data.initialReduxState.pins[pin].comments:
                            comments_file = f"{os.path.splitext(os.path.basename(image_url))[0]}_comments.txt"
                            comments_path = os.path.join(os.getcwd(), folder_name, comments_file)
                            with open(comments_path, "w", encoding="utf-8") as f:
                                for comment in data.initialReduxState.pins[pin].comments:
                                    f.write(comment.get("text") + "\n")
                            break
            except Exception:
                continue

### Run the code ###
import random
import time
import queue
from scrapy.crawler import CrawlerProcess
from pydispatch import dispatcher
from scrapy import signals

def on_spider_closed(spider, reason):
    if reason == 'finished':
        if len(spider.unique_img) > 0:
            print(f"Spider finished successfully! Downloaded {len(spider.unique_img)} images. Images are saved in '{spider.output_folder}'")
        else:
            print("Spider finished successfully, but no images were downloaded.")
    else:
        print(f"Spider failed with reason: {reason}")

    if not keyword_queue.empty():
        schedule_next_crawl()

dispatcher.connect(on_spider_closed, signal=signals.spider_closed)

def read_keywords(file_path):
    with open(file_path, 'r') as file:
        keywords = file.read().strip().split(',')
    return keywords

def schedule_next_crawl():
    keyword = keyword_queue.get()
    time_to_sleep = random.randint(1, 3)  
    print(f"Scheduled crawl for keyword '{keyword.strip()}'. Waiting for {time_to_sleep} seconds before scheduling the next one...")
    process.crawl(PinterestSpider, keyword=keyword.strip(), output_folder='bigTest')
    time.sleep(time_to_sleep)
    process.start()

if __name__ == '__main__':
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    })

    keyword_queue = queue.Queue()
    keywords = read_keywords('keyword.txt')
    for keyword in keywords:
        keyword_queue.put(keyword.strip())

    schedule_next_crawl()
