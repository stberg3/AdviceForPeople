import scrapy
from pymongo import MongoClient

class SlateSpider(scrapy.Spider):
    name = "slate"
    DB_NAME = "advice_articles"
    COL_NAME = "dear_prudence"

    def start_requests(self):
        print("STARTING")
        client = MongoClient()
        collection = client[self.DB_NAME][self.COL_NAME]

        urls = [{'loc': item['loc'], "id": item["_id"]} for item in collection.find()][:2]

        for url in urls:
            req = scrapy.Request(url=url['loc'], callback=self.parse)
            req.meta['id'] = url['id']
            yield req

    def parse(self, response):
        id = response.meta['id']
        print("PARSING", id)
        article = response.xpath("//article[@id='story-0']")
        all_paragraphs = article.xpath("//div[contains(@class, 'parbase')]")
        article_delimiters = []
        temp_delimiter = dict()

        parsed_articles = {
            "title" : response.xpath("//h1[@class='hed']/text()").extract_first(),
            "subtitle" : response.xpath("//h2[@class='dek']/text()").extract_first(),
            "author" : response.xpath("//a[@rel='author']/text()").extract_first(),
            "id" : id,
            "questions" : []
        }

        # Get indices for start/end of questions and end of answers
        for index in range(len(all_paragraphs)):
            element = all_paragraphs[index]
            title = element.xpath(".//p/strong/text()").extract_first()
            string = element.xpath(".//p/text()").extract_first()

            if title and title.startswith("Dear Prudence,"):
                temp_delimiter["start_index"] = index
            elif string and string.startswith("—"):
                temp_delimiter['end_question'] = index
            else:
                strong = element.xpath(".//strong/text()").extract_first()
                soft = element.xpath(".//p/text()").extract_first()
                if "start_index" in temp_delimiter.keys() and string == '* * *':
                    temp_delimiter['end_index'] = index
                    article_delimiters.append(temp_delimiter)
                    temp_delimiter = dict()

        # Extract the articles based on the indices
        for delim_dict in article_delimiters:
            parsed_article = dict()
            question = ""
            alias = None
            answer = ""

            q_block = all_paragraphs[delim_dict['start_index']:delim_dict['end_question']]
            alias = all_paragraphs[delim_dict['end_question']].xpath(".//p/text()").extract_first()[1:]
            a_block = all_paragraphs[delim_dict['end_question']+1:delim_dict['end_index']]

            for p in q_block:
                question += p.xpath(".//p").extract_first()

            for p in a_block:
                answer += p.xpath(".//p").extract_first()

            parsed_article['question'] = question
            parsed_article['alias'] = alias
            parsed_article['answer'] = answer

            parsed_articles["questions"].append(parsed_article)

        return parsed_articles
