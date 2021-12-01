import datetime
import operator

from bs4 import BeautifulSoup
import time
import csv
import asyncio
import aiohttp
import pymongo

MONGO = "mongodb+srv://admin:admin@cluster0.bwhk4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
URL = "https://v1.ru/text/"
HEADERS = {
    "Accept": "text / html, application / xhtml + xml, application / xml; q = 0.9, image / avif, image / webp, * / *;q = 0.8",
    "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64; rv: 94.0) Gecko / 20100101 Firefox / 94.0"
}
PATH = "news_async.csv"
ID = 1

async def getPageData(session, page, pagesCount, news):
    async with session.get(url=f"{URL}?page={page}", headers=HEADERS) as response:
        responseText = await response.text()
        await parsePage(session, news, responseText)
        print(f"[INFO] Парсинг страницы {pagesCount + 1 - page} из {pagesCount}")


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
        for page in range(pagesCount, 0, -1):
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

        # Сохраняем данные в базу данных (обновляем старые)
        print(f"[INFO] Сохранение в БД...")
        client = pymongo.MongoClient(MONGO)
        db = client.V1News
        coll = db.news
        docs_count = coll.count_documents({})

        ## Сортируем список по датам
        news.sort(key=operator.itemgetter("Date"))
        for i in range(0, len(news)):
            news[i]["_id"] = i + 1

        for id in range(1, len(news) + 1):
            if id > docs_count:
                coll.insert_one(news[id - 1])
            else:
                current = {"Id": id}
                new = {"$set": {"Views": news[id - 1]["Views"],
                                "Comments": news[id - 1]["Comments"]}}
                coll.update_one(current, new)
        print("[INFO] Успешно!")
    except Exception as ex:
        print(f"[ERROR] {ex}")


async def parsePage(session, news: list, html):
    HOST = "https://v1.ru"
    soup = BeautifulSoup(html, "html.parser")
    items = soup.findAll("article", "IJamp")
    for item in reversed(items):
        heading = None; date = None; link = None; views = None; comments = None;    # очищаем переменные
        heading = item.find("h2", "IJm9").getText(strip=True)                       # получаем название новости
        if item.find("div", "IJal3") is None:                                       # eсли нет краткого описания,
            continue                                                                #   значит, это просто реклама - пропускаем ее,
        else:                                                                       # иначе получаем краткое описание новости
            description = item.find("div", "IJal3").getText(strip=True)
        date = datetime.datetime\
            .fromisoformat(item.find("div", "IJain IJam-")                          # получаем дату
                                .find("time").get("datetime"))
        link = item.find("h2", "IJm9").find("a").get("href")                        # получаем ссылку на статью
        if link.find("v1.ru") == -1:                                                # если ссылка не содержит в себе хоста,
            link = HOST + link                                                      #   то добавляем его
        content = await parseNewsContent(session, link)                                   # парсим содержимое статьи
        stats = item.findAll("span", "H3gt")                                        # получаем данные о просмотрах и комментариях
        views = stats[0].getText(strip=True)
        if len(stats) < 2 or stats[1].getText(strip=True).find("Обсудить") != -1:   # если комментариев еще нет,
            comments = ""                                                           #   записываем пустую строку
        else:                                                                       # иначе парсим кол-во комментариев
            comments = stats[1].getText(strip=True)
        global ID
        news.append({                                                               # добавляем все данные о статье в список
            "_id": ID,
            "Heading": heading,
            "Description": description,
            "Date": date,
            "Link": link,
            "Content": content,
            "Views": views,
            "Comments": comments
        })
        ID += 1


# Парсинг содержимого статьи
async def parseNewsContent(session, URL):
    async with session.get(url=URL, headers=HEADERS) as response:
        responseText = await response.text()
        soup = BeautifulSoup(responseText, "html.parser")
        try:
            contentList = soup.find("div", "I5pv").findAll("div", "INant")  # находим все абзацы статьи
        except:
            contentList = []
        result = ""
        for content in contentList:                                         # записываем все абзацы в одну строку
            result += content.getText(strip=True, separator=" ") + "\n"
        return result


# Сохранение новостей в файл CSV
def saveCSV(newsList: list, path: str):
    with open(path, "w", newline="", encoding="cp1251", errors="ignore") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Заголовок", "Описание", "Дата", "Ссылка", "Содержание", "Количество просмотров", "Количество комментариев"])
        for news in newsList:
            writer.writerow([news["Heading"], news["Description"], news["Date"], news["Link"], news["Content"], news["Views"], news["Comments"]])


if __name__ == '__main__':
    main()

