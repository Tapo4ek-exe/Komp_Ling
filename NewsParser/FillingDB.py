import csv
import datetime
import operator
import os
import pymongo
import Config


def main():
    news = []
    print(f"[{currentTime()}] [INFO] Считывание новстей...")

    # Считывание новостей из CSV
    ## Подготовка списка путей
    index = 1
    while os.path.exists(f"{Config.PATH}/news{index}.csv"):
        news.extend(readCSV(f"{Config.PATH}/news{index}.csv"))
        index += 1
    if os.path.exists(f"{Config.PATH}/{Config.FILENAME}"):
        news.extend(readCSV(f"{Config.PATH}/{Config.FILENAME}"))


    # Сохраняем данные в базу данных (обновляем старые)
    print(f"[{currentTime()}] [INFO] Сохранение в БД...")
    client = pymongo.MongoClient(Config.MONGO)
    db = client.V1News
    coll = db.news

    ## Сортируем список по датам
    news.sort(key=operator.itemgetter("Date"))
    for i in range(0, len(news)):
        news[i]["_id"] = i + 1

    ## Сохранение полученных данных
    docs_count = coll.count_documents({})
    for id in range(1, len(news) + 1):
        if id > docs_count:
            coll.insert_one(news[id - 1])
        else:
            current = {"Id" : id}
            new = {"$set": {"Views": news[id - 1]["Views"],
                            "Comments": news[id - 1]["Comments"]}}
            coll.update_one(current, new)

    print(f"[{currentTime()}] [INFO] Успешно!")


# Считывание нвостей из файла CSV
def readCSV(path):
    news = []
    with open(path, "r", newline="", encoding="cp1251", errors="ignore") as file:
        reader = csv.reader(file, delimiter=";")
        isFirst = True
        for row in reader:
            if isFirst:
                isFirst = False
                continue
            news.append({
                "_id": Config.ID,
                "Heading": row[0],
                "Description": row[1],
                "Date": row[2],
                "Link": row[3],
                "Content": row[4],
                "Views": row[5],
                "Comments": row[6]
            })
            Config.ID += 1
    return news


# Получение текущего времени в виде строки
def currentTime():
    return datetime.datetime.now().strftime("%H:%M:%S")

if __name__=="__main__":
    main()