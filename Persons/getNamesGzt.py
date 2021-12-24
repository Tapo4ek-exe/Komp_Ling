import time

from bs4 import BeautifulSoup
import requests
from selenium import webdriver

def getPersons():
    headers = {
        "Accept": "text / html, application / xhtml + xml, application / xml; q = 0.9, image / avif, image / webp, * / *;q = 0.8",
        "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64; rv: 95.0) Gecko / 20100101 Firefox / 95.0"
    }
    url = "http://global-volgograd.ru/person"
    host = "http://global-volgograd.ru"

    response = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    pages = soup.find("div", "pager").find_all("li", "pager-item")
    FIO = []
    isFirst = True
    for page in pages:
        if isFirst:
            parsePersons(soup, FIO)
            isFirst = False
        else:
            url = host + page.find("a").get("href")
            response = requests.get(url=url, headers=headers)
            while response.status_code != 200:
                response = requests.get(url=url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            parsePersons(soup, FIO)

    with open("algfio/persons.gzt", "w", encoding="utf-8", errors="ignore") as file:
        id = 1
        for fio in FIO:
            fio_split = fio.split(" ")
            file.write(f"PersonsNames \"{fio_split[1]}_{fio_split[0]}_{id}\"\n")
            file.write("{\n\tkey = ")
            if len(fio_split) == 2:
                file.write(f"\"{fio}\"")
                file.write(f" | \"{fio_split[1]} {fio_split[0]}\"")
            else:
                file.write(f"\"{fio}\"")
                file.write(f" | \"{fio_split[1]} {fio_split[2]} {fio_split[0]}\"")
                file.write(f" | \"{fio_split[0]} {fio_split[1]}\"")
                file.write(f" | \"{fio_split[1]} {fio_split[0]}\"")
            file.write(";\n\tlemma = ")
            file.write(f" \"{fio_split[1]} {fio_split[0]}\";")
            file.write("\n}\n\n")
            id += 1


def parsePersons(soup, FIO):
    items = soup.find_all("div", "person-block")
    for item in items:
        fio = item.find("div", "title").get_text(strip=True)
        fio = fio.split(" ")
        fio[0] = fio[0].capitalize()
        if len(fio) == 3:
            fio = fio[0] + " " + fio[1] + " " + fio[2]
        else:
            fio = fio[0] + " " + fio[1]
        FIO.append(fio)


def getAttractions():
    driver = webdriver.Chrome()
    attractions = []
    try:
        url = "https://avolgograd.com/sights?obl=vgg"
        driver.get(url)
        driver.find_element_by_id("true-loadmore").click()
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.find_all("div", "ta-f-box ta-f-box-cat")
        for item in items:
            attractions.append(item.find("div", "ta-200").find("div", "ta-211").get_text(strip=True))
    except Exception as ex:
        print(ex)
    finally:
        driver.close()

    with open("algfio/attractions.gzt", "w", encoding="utf-8", errors="ignore") as file:
        for attraction in attractions:
            attraction = attraction.replace("\"", "")
            file.write(f"AttractionsNames \"{attraction.replace(' ', '_')}\"\n")
            file.write("{\n\tkey = ")
            file.write(f"\"{attraction}\";\n\tlemma = \"{attraction}\";\n")
            file.write("}\n\n")

if __name__=="__main__":
    getPersons()
    getAttractions()
