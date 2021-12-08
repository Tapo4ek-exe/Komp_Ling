import datetime
import os
from progress.bar import IncrementalBar
from bs4 import BeautifulSoup
import requests
import time
import csv
import Config


soupSourcesId = 0


# Парсинг нвостей с сайта V1.RU
def main():
    # Определяем кол-во страниц
    response = requests.get(url=Config.URL, headers=Config.HEADERS)
    while response.status_code != 200:
        time.sleep(3)
        response = requests.get(url=Config.URL, headers=Config.HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    ## Определяем нужный набор классов для парсинга
    paginationBar = None
    global soupSourcesId
    while paginationBar is None and soupSourcesId < len(Config.soupSources):
        paginationBar = soup.find("div", Config.soupSources[soupSourcesId]["PaginationBar"])
        soupSourcesId += 1
    if paginationBar is None:
        print(f"[{currentTime()}] [ERROR] Названия классов изменились. Парсинг невозможен!")
        return
    soupSourcesId -= 1
    pagesCount = int(paginationBar.findAll("div", Config.soupSources[soupSourcesId]["Pages"])[-1].getText(strip=True))
    if Config.END == 0 or Config.END > pagesCount:
        Config.END = pagesCount + 1

    if not os.path.exists(Config.PATH):
        os.mkdir(Config.PATH)

    # Парсим все страницы
    try:
        news = []
        startTime = time.time()
        for pageNumber in range(Config.START, Config.END):
            response = requests.get(url=f"{Config.URL}?page={pageNumber}", headers=Config.HEADERS)
            while response.status_code != 200:
                response = requests.get(url=f"{Config.URL}?page={pageNumber}", headers=Config.HEADERS)
                time.sleep(3)
            parsePage(news, response.text, pageNumber, pagesCount)
            if Config.SAVE_EVERY != 0 and pageNumber % Config.SAVE_EVERY == 0:
                saveCSV(news, f"{Config.PATH}/news{pageNumber//Config.SAVE_EVERY}.csv")
                news.clear()
        endTime = time.time()
        print(f"[{currentTime()}] [INFO] Прошло времени: {endTime - startTime} сек")
    except Exception as ex:
        print(ex)
    finally:
        saveCSV(news, f"{Config.PATH}/{Config.FILENAME}")

    print(f"[{currentTime()}] [INFO] Успешно!")


# Парсинг страницы с новостями V1.RU
def parsePage(news: list, html, pageNumber, pagesCount):
    # Получение названий классов для парсинга
    articles_class = Config.soupSources[soupSourcesId]["Articles"]
    heading_class = Config.soupSources[soupSourcesId]["Heading"]
    desc_class = Config.soupSources[soupSourcesId]["Description"]
    date_class = Config.soupSources[soupSourcesId]["Date"]
    stats_class = Config.soupSources[soupSourcesId]["Stats"]

    HOST = "https://v1.ru"
    soup = BeautifulSoup(html, "html.parser")
    items = soup.findAll("article", articles_class)
    bar = IncrementalBar(f"[{currentTime()}] [INFO] Парсинг страницы {pageNumber} из {pagesCount}", max=len(items)*7)
    for item in items:
        heading = None; date = None; link = None; views = None; comments = None;    # очищаем переменные
        heading = item.find("h2", heading_class).getText(strip=True); bar.next()    # получаем название новости
        description = item.find("div", desc_class)
        if description is None:                                                     # eсли нет краткого описания,
            bar.finish()
            continue                                                                #   значит, это просто реклама - пропускаем ее,
        else:                                                                       # иначе получаем краткое описание новости
            description = description.getText(strip=True)
            bar.next()
        date = datetime.datetime\
            .fromisoformat(item.find("div", date_class)                             # получаем дату
                                .find("time").get("datetime"))
        bar.next()
        link = item.find("h2", heading_class).find("a").get("href"); bar.next()     # получаем ссылку на статью
        if link.find("v1.ru") == -1:                                                # если ссылка не содержит в себе хоста,
            link = HOST + link                                                      #   то добавляем его
        content = parseNewsContent(link); bar.next()                                # парсим содержимое статьи
        stats = item.findAll("span", stats_class)                                   # получаем данные о просмотрах и комментариях
        views = stats[0].getText(strip=True); bar.next()
        if len(stats) < 2 or stats[1].getText(strip=True).find("Обсудить") != -1:   # если комментариев еще нет,
            comments = ""                                                           #   записываем пустую строку
        else:                                                                       # иначе парсим кол-во комментариев
            comments = stats[1].getText(strip=True)
        bar.next()
        news.append({                                                               # добавляем все данные о статье в список
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
def parseNewsContent(URL):
    # Получение имен классов для парсинга
    content_class = Config.soupSources[soupSourcesId]["ContentAll"]
    contentPar_class = Config.soupSources[soupSourcesId]["ContentPar"]

    # Находим все абзацы статьи
    response = requests.get(url=URL, headers=Config.HEADERS)
    while response.status_code != 200:
        time.sleep(3)
        response = requests.get(url=URL, headers=Config.HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    try:
        contentList = soup.find("div", content_class)\
            .findAll("div", contentPar_class)
    except:
        contentList = []
    result = ""

    # Записываем все абзацы в одну строку
    for content in contentList:
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

