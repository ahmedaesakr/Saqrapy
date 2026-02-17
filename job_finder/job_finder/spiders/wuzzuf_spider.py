
import scrapy
import re
from urllib.parse import urlencode
from job_finder.cv_config import RELEVANT_KEYWORDS, SEARCH_KEYWORDS, is_relevant

class WuzzufSpider(scrapy.Spider):
    name = "wuzzuf_jobs"

    # Base search URL for Wuzzuf
    base_url = "https://wuzzuf.net/search/jobs/?"

    # Use centralized search keywords from cv_config
    keywords = SEARCH_KEYWORDS

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS

    def start_requests(self):
        for keyword in self.keywords:
            params = {
                'key': keyword,
                'a': 'hpb', # hidden parameter
                # You can add more parameters here if Wuzzuf supports them in URL query
                # e.g., location, type etc if known. For now, general search.
            }
            url = f"{self.base_url}{urlencode(params)}"
            yield scrapy.Request(url, callback=self.parse, meta={'keyword': keyword})



    def parse(self, response):
        self.logger.info(f"Scraping URL: {response.url}")
        
        # Select job cards based on 'css-ghe2tq' class found in inspection
        job_cards = response.css('div.css-ghe2tq')
        
        if not job_cards:
            self.logger.warning("No job cards found with selector div.css-ghe2tq")
        
        for card in job_cards:
            title = card.css('h2.css-193uk2c a::text').get()
            link = card.css('h2.css-193uk2c a::attr(href)').get()
            company = card.css('a.css-ipsyv7::text').get()
            location = card.css('span.css-16x61xq::text').get()
            job_type = card.css('span.css-uc9rga::text').get()
            

            # Strict Filtering: Check if title is relevant
            # Use regex for word boundaries to avoid partial matches like "Waiter" (AI) or "Sustainability" (AI)
            
            # Create a combined regex pattern: \b(Designer|3D|...)\b
            pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
            
            if not is_relevant(title=title):
                self.logger.info(f"Skipping irrelevant title: {title}")
                continue


            # Cleaning up company name (it often has " -" at the end)
            if company:
                company = company.replace('-', '').strip()

            item = {
                'keyword_searched': response.meta.get('keyword'),
                'title': title,
                'company': company,
                'location': location,
                'type': job_type,
                'link': link,
                'source': 'Wuzzuf'
            }
            
            yield item

        
        # Pagination: Look for a "Next" button. 
        # In the HTML, there are buttons with class 'css-1y7kjgo' or links ?start=X
        # A simple way is to check the 'start' param and increment if we found jobs.
        # But let's check for the actual 'next' element if possible.
        # Inspecting HTML for pagination: <button class="css-1y7kjgo ..."><a href="...?start=1">2</a></button>
        # The 'next' button usually is the one after the current active one, or just the last one.
        # Wuzzuf pagination often works by `start=N*pageSize`. 
        # Let's try to find the 'next' page link generically.
        
        current_url = response.url
        if "start=" in current_url:
            current_start = int(current_url.split("start=")[1].split("&")[0])
            next_start = current_start + 1 # Wuzzuf pages seem to be 0, 1, 2... based on the links ?start=1, ?start=2
        else:
            current_start = 0
            next_start = 1
            
        # Limit pages to avoid infinite loops for this test
        if next_start < 5 and job_cards:
             # Construct next URL
             if "start=" in current_url:
                 next_page = current_url.replace(f"start={current_start}", f"start={next_start}")
             else:
                 next_page = f"{current_url}&start={next_start}"
                 
             yield scrapy.Request(next_page, callback=self.parse, meta=response.meta)

        next_page = response.css('a.css-1246l8h::attr(href)').get() # Generic 'Next' arrow class?
        # Or usually it's easier to increment 'start' param programmatically or follow specific link.
        
        # Let's try to follow the 'Next' button if found in typical Wuzzuf pagination
        # (This selector is an educated guess based on Wuzzuf structure, might need adjustment)
        if next_page:
             yield response.follow(next_page, callback=self.parse, meta=response.meta)

