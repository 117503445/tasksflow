import tasksflow.pool
import tasksflow.task
from lxml import etree
import requests

from loguru import logger

logger.enable("tasksflow")


class TaskRequest(tasksflow.task.Task):
    def run(self):
        print("TaskRequest")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        d_page_resp: dict[int, str] = {}
        for page in range(1, 3):
            url = "http://hackernews.cc/page/{}".format(page)
            resp = requests.get(url, headers=headers).text
            d_page_resp[page] = resp
        return {"d_page_resp": d_page_resp}


class TaskParse(tasksflow.task.Task):
    def run(self, d_page_resp: dict[int, str]):
        d_page_title: dict[int, str] = {}
        for page, resp in d_page_resp.items():
            tree = etree.HTML(resp, etree.HTMLParser())
            title = tree.xpath('//h3[@class="classic-list-title"]/a/text()')
            d_page_title[page] = title
        print(f"d_page_title: {d_page_title}")
        return {"d_page_title": d_page_title}


def main():
    tasks = [TaskRequest(), TaskParse()]
    p = tasksflow.pool.Pool(tasks)
    result = p.run()
    print(f"result: {result}")


if __name__ == "__main__":
    main()
