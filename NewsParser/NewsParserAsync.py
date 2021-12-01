from bs4 import BeautifulSoup
import requests
import time
import csv
import asyncio
import aiohttp

URL = "https://v1.ru/text/"
HEADERS = {
    "Accept": "text / html, application / xhtml + xml, application / xml; q = 0.9, image / avif, image / webp, * / *;q = 0.8",
    "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64; rv: 94.0) Gecko / 20100101 Firefox / 94.0"
}
PATH = "news_async.csv"

async def getPageData(session, page, pagesCount, news):
    async with session.get(url=f"{URL}?page={page}", headers=HEADERS) as response:
        responseText = await response.text()
        await parsePage(session, news, responseText)
        print(f"[INFO] Парсинг страницы {page} из {pagesCount}")


async def gatherData(news):
    async with aiohttp.ClientSession() as session:
        # Определяем кол-во страниц
        response = await session.get(url=URL, headers=HEADERS)
        responseText = await response.text()
        soup = BeautifulSoup(responseText, "html.parser")
        paginationBar = soup.find("div", "HRahz PZm3")
        pagesCount = int(paginationBar.findAll("div", "HRah1")[-1].getText(strip=True))

        # Парсим все страницы
        tasks = []
        pagesCount = 10
        for page in range(1, pagesCount + 1):
            task = asyncio.create_task(getPageData(session, page, pagesCount, news))
            tasks.append(task)

        await asyncio.gather(*tasks)


# Парсинг нвостей с сайта V1.RU
def main():
    try:
        startTime = time.time()
        news = []
        asyncio.get_event_loop().run_until_complete(gatherData(news))
        endTime = time.time()
        print(f"[INFO] Прошло времени: {endTime - startTime} сек")
        saveCSV(news, PATH)
    except Exception as ex:
        print(ex)



async def parsePage(session, news: list, html):
    HOST = "https://v1.ru"
    soup = BeautifulSoup(html, "html.parser")
    items = soup.findAll("article", "IJamp")
    for item in items:
        heading = None; date = None; link = None; views = None; comments = None;
        heading = item.find("h2", "IJm9").getText(strip=True)
        if item.find("div", "IJal3") is None:
            continue
        else:
            description = item.find("div", "IJal3").getText(strip=True)
        date = item.find("div", "IJain IJam-").getText(strip=True)
        link = item.find("h2", "IJm9").find("a").get("href")
        if link.find("v1.ru") == -1:
            link = HOST + link
        content = await parseNewsContent(session, link)
        stats = item.findAll("span", "H3gt")
        views = stats[0].getText(strip=True)
        if len(stats) < 2 or stats[1].getText(strip=True).find("Обсудить") != -1:
            comments = ""
        else:
            comments = stats[1].getText(strip=True)

        news.append({
            "Heading": heading,
            "Description": description,
            "Date": date,
            "Link": link,
            "Content": content,
            "Views": views,
            "Comments": comments
        })


async def parseNewsContent(session, URL):
    async with session.get(url=URL, headers=HEADERS) as response:
        responseText = await response.text()
        soup = BeautifulSoup(responseText, "html.parser")
        try:
            contentList = soup.find("div", "I5pv").findAll("div", "INant")
        except:
            contentList = []
        result = ""
        for content in contentList:
            result += content.getText(strip=True, separator=" ") + "\n"
        return result


def saveCSV(newsList: list, path: str):
    with open(path, "w", newline="", encoding="cp1251", errors="ignore") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Заголовок", "Описание", "Дата", "Ссылка", "Содержание", "Количество просмотров", "Количество комментариев"])
        for news in newsList:
            writer.writerow([news["Heading"], news["Description"], news["Date"], news["Link"], news["Content"], news["Views"], news["Comments"]])


if __name__ == '__main__':
    main()

