from bs4 import BeautifulSoup
import requests
import time
import csv

URL = "https://v1.ru/text/"
HEADERS = {
    "Accept": "text / html, application / xhtml + xml, application / xml; q = 0.9, image / avif, image / webp, * / *;q = 0.8",
    "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64; rv: 94.0) Gecko / 20100101 Firefox / 94.0"
}
PATH = "news.csv"

# Парсинг нвостей с сайта V1.RU
def main():
    # Определяем кол-во страниц
    response = requests.get(url=URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    paginationBar = soup.find("div", "HRahz PZm3")
    pagesCount = int (paginationBar.findAll("div", "HRah1")[-1].getText(strip=True))

    # Парсим все страницы
    news = []
    pagesCount = 10
    startTime = time.time()
    for pageNumber in range(1, pagesCount + 1):
        print(f"[INFO] Парсинг страницы {pageNumber} из {pagesCount}")
        response = requests.get(url=f"{URL}?page={pageNumber}", headers=HEADERS)
        parsePage(news, response.text)
    endTime = time.time()
    print(f"[INFO] Прошло времени: {endTime - startTime} сек")
    saveCSV(news, PATH)
    print(news[0]["Content"])


def parsePage(news: list, html):
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
        content = parseNewsContent(link)
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

def parseNewsContent(URL):
    response = requests.get(url=URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
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

