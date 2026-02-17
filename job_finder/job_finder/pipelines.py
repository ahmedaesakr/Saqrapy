# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from itemadapter import ItemAdapter


class CleaningPipeline:
    """Strip whitespace from all string fields"""
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        for field_name in adapter.field_names():
            value = adapter.get(field_name)
            if isinstance(value, str):
                adapter[field_name] = value.strip()
        return item


class DeduplicationPipeline:
    """Drop duplicate items based on link URL"""
    def __init__(self):
        self.seen_links = set()

    def process_item(self, item, spider):
        from scrapy.exceptions import DropItem
        adapter = ItemAdapter(item)
        link = adapter.get('link')
        if link and link in self.seen_links:
            raise DropItem(f"Duplicate: {link}")
        if link:
            self.seen_links.add(link)
        return item


class RelevanceScoringPipeline:
    """Score each job item against Ahmed's CV profile.

    - Adds 'relevance_score' (0-100) to every item
    - Drops items that match NEGATIVE_KEYWORDS (score=0)
    - Logs score distribution at spider close
    """

    def __init__(self):
        self.score_counts = {'high': 0, 'medium': 0, 'low': 0, 'dropped': 0}

    def process_item(self, item, spider):
        from scrapy.exceptions import DropItem
        from job_finder.cv_config import score_job

        adapter = ItemAdapter(item)
        title = adapter.get('title', '') or ''
        description = adapter.get('description', '') or adapter.get('full_text', '') or ''
        location = adapter.get('location', '') or ''
        job_type = adapter.get('type', '') or ''

        score = score_job(title=title, description=description,
                          location=location, job_type=job_type)
        adapter['relevance_score'] = score

        if score == 0:
            self.score_counts['dropped'] += 1
            raise DropItem(f"Irrelevant (negative keyword): {title}")

        if score >= 60:
            self.score_counts['high'] += 1
        elif score >= 30:
            self.score_counts['medium'] += 1
        else:
            self.score_counts['low'] += 1

        return item

    def close_spider(self, spider):
        total = sum(self.score_counts.values())
        if total > 0:
            spider.logger.info(
                f"Relevance scores: {self.score_counts['high']} excellent, "
                f"{self.score_counts['medium']} good, "
                f"{self.score_counts['low']} weak, "
                f"{self.score_counts['dropped']} dropped | Total: {total}"
            )
