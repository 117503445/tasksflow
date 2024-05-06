import tasksflow.pool
import tasksflow.task
from lxml import etree
import requests

from loguru import logger

# logger.enable("tasksflow")


class TaskRequest(tasksflow.task.Task):
    def run(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        url = "https://webscraper.io/test-sites"
        resp = requests.get(url, headers=headers).text
        return {"resp": resp}


class TaskParse(tasksflow.task.Task):
    def run(self, resp: str):
        html = etree.HTML(resp, etree.HTMLParser())
        title_elements = html.xpath("/html/body/div[1]/div[3]/div[*]/div[1]/h2/a")
        titles = [title.text.strip() for title in title_elements]
        return {"titles": titles}


def main():
    tasks = [TaskRequest(), TaskParse()]
    p = tasksflow.pool.Pool(tasks)
    result = p.run()
    print(f"titles: {result['titles']}")


if __name__ == "__main__":
    main()
