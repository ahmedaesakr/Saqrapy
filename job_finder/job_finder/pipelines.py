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
