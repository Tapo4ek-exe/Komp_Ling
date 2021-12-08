import datetime
from progress.bar import IncrementalBar
from bs4 import BeautifulSoup
import time
import csv
import asyncio
import aiohttp
import Config


soupSourcesId = 0


async def getPageData(session, page, pagesCount, news, retry=5):
    try:
        response = await session.get(url=f"{Config.URL}?page={page}", headers=Config.HEADERS)
        while response.status != 200:
            time.sleep(3)
            response = await session.get(url=f"{Config.URL}?page={page}", headers=Config.HEADERS)
        responseText = await response.text()
        print("")
        await parsePage(session, news, responseText, page, pagesCount)
        if Config.SAVE_EVERY != 0 and page % Config.SAVE_EVERY == 0:
            saveCSV(news, f"{Config.PATH}/news{page // Config.SAVE_EVERY}.csv")
            news.clear()
    except Exception as ex:
        if retry > 0:
            print(f"[{currentTime()}] [WARNING] Не удается загрузить страницу {page}")
            print(f"[{currentTime()}] [WARNING] Попытка переподключения {6 - retry} из 5")
            time.sleep(5)
            await getPageData(session, page, pagesCount, news, retry-1)
        else:
            print(f"[{currentTime()}] [ERROR] {ex}")


async def gatherData(news):
    connector = aiohttp.TCPConnector(limit=50, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Определяем кол-во страниц
        response = await session.get(url=Config.URL, headers=Config.HEADERS)
        while response.status != 200:
            time.sleep(3)
            response = await session.get(url=Config.URL, headers=Config.HEADERS)
        responseText = await response.text()
        soup = BeautifulSoup(responseText, "html.parser")

        ## Определяем нужный набор классов для парсинга
        paginationBar = None
        global soupSourcesId
        while paginationBar is None and soupSourcesId < len(Config.soupSources):
            paginationBar = soup.find("div", Config.soupSources[soupSourcesId]["PaginationBar"])
            soupSourcesId += 1
        if paginationBar is None:
            print(f"[{currentTime()}] [ERROR] Названия классов изменились. Парсинг невозможен!")
            return None
        soupSourcesId -= 1
        pagesCount = int(paginationBar.findAll("div", Config.soupSources[soupSourcesId]["Pages"])[-1].getText(strip=True))
        if Config.END == 0 or Config.END > pagesCount:
            Config.END = pagesCount + 1

        # Парсим все страницы
        tasks = []
        for page in range(Config.START, Config.END):
            task = asyncio.create_task(getPageData(session, page, pagesCount, news))
            tasks.append(task)

        await asyncio.gather(*tasks)


# Парсинг нвостей с сайта V1.RU
def main():
    news = []

    startTime = time.time()
    print(f"[{currentTime()}] [INFO] Подготовка к парсингу")
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)
    asyncio.get_event_loop().run_until_complete(gatherData(news))
    endTime = time.time()
    print(f"[{currentTime()}] [INFO] Прошло времени: {endTime - startTime} сек")
    saveCSV(news, Config.PATH)
    print(f"[{currentTime()}] [INFO] Успешно!")


async def parsePage(session, news: list, html, pageNumber, pagesCount):
    HOST = "https://v1.ru"
    soup = BeautifulSoup(html, "html.parser")
    items = soup.findAll("article", Config.soupSources[soupSourcesId]["Articles"])
    bar = IncrementalBar(f"[{currentTime()}] [INFO] Парсинг страницы {pageNumber} из {pagesCount}", max=len(items) * 7)
    for item in reversed(items):
        heading = None; date = None; link = None; views = None; comments = None;                        # очищаем переменные
        heading = item.find("h2", Config.soupSources[soupSourcesId]["Heading"]).getText(strip=True)     # получаем название новости
        bar.next()
        if item.find("div", Config.soupSources[soupSourcesId]["Description"]) is None:                  # eсли нет краткого описания,
            continue                                                                                    #   значит, это просто реклама - пропускаем ее,
        else:                                                                                           # иначе получаем краткое описание новости
            description = item.find("div", Config.soupSources[soupSourcesId]["Description"]).getText(strip=True)
        bar.next()
        date = datetime.datetime\
            .fromisoformat(item.find("div", Config.soupSources[soupSourcesId]["Date"])                  # получаем дату
                                .find("time").get("datetime"))
        bar.next()
        link = item.find("h2", Config.soupSources[soupSourcesId]["Heading"]).find("a").get("href")      # получаем ссылку на статью
        if link.find("v1.ru") == -1:                                                                    # если ссылка не содержит в себе хоста,
            link = HOST + link                                                                          #   то добавляем его
        bar.next()
        content = await parseNewsContent(session, link)                                                 # парсим содержимое статьи
        bar.next()
        stats = item.findAll("span", Config.soupSources[soupSourcesId]["Stats"])                        # получаем данные о просмотрах и комментариях
        views = stats[0].getText(strip=True)
        bar.next()
        if len(stats) < 2 or stats[1].getText(strip=True).find("Обсудить") != -1:                       # если комментариев еще нет,
            comments = ""                                                                               #   записываем пустую строку
        else:                                                                                           # иначе парсим кол-во комментариев
            comments = stats[1].getText(strip=True)
        bar.next()

        news.append({                                                                                   # добавляем все данные о статье в список
            "_id": Config.ID,
            "Heading": heading,
            "Description": description,
            "Date": date,
            "Link": link,
            "Content": content,
            "Views": views,
            "Comments": comments
        })
        Config.ID += 1
        bar.finish()


# Парсинг содержимого статьи
async def parseNewsContent(session, URL):
    async with session.get(url=URL, headers=Config.HEADERS) as response:
        while response.status != 200:
            time.sleep(3)
            response = await session.get(url=URL, headers=Config.HEADERS)
        responseText = await response.text()
        soup = BeautifulSoup(responseText, "html.parser")
        try:
            contentList = soup.find("div", Config.soupSources[soupSourcesId]["ContentAll"])\
                .findAll("div", Config.soupSources[soupSourcesId]["ContentPar"])    # находим все абзацы статьи
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


# Получение текущего времени в виде строки
def currentTime():
    return datetime.datetime.now().strftime("%H:%M:%S")


if __name__ == '__main__':
    main()

