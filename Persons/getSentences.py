import os
import time

import pymongo
import re


def main():
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.bwhk4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = client.V1News
    coll = db.news
    curent = 1
    newsCount = coll.count_documents({})
    counter = -1
    facts = []
    try:
        for news in coll.find().sort("_id", pymongo.DESCENDING):
            # Подготавливаем статью для томита-парсера
            print(f"[INFO] Обработка статьи {curent} из {newsCount}")
            print(news["Heading"])
            counter -= 1
            split_regex = re.compile(r'[.|!|?|…]')
            sentences = filter(lambda t: t, [t.strip() for t in split_regex.split(news["Content"].strip())])
            with open("algfio/test.txt", "w", encoding="utf-8") as file:
                for s in sentences:
                    file.write(s + ".\n")

            # Вызываем томита-парсер
            os.system("./tomita-parser ./algfio/config.proto")

            # Отбираем предложения с личностями и достопримечательностями
            with open("algfio/facts.txt", "r", encoding="utf-8") as file:
                sentence = ""
                personName = ""
                attractionName = ""
                personFound = False
                attractionFound = False
                for line in file:
                    if line.find("Person") != -1:
                        personFound = True
                        continue
                    elif line.find("AttractionObj") != -1:
                        attractionFound = True
                        continue
                    elif line.find("{") != -1 or line.find("}") != -1:
                        continue
                    elif line.find("Name") != -1:
                        if personFound:
                            personName = line[line.index("Name") + 6:]
                            personName_split = personName.split(" ")
                            personName = ""
                            for s in personName_split:
                                personName += s.capitalize() + " "
                            personFound = False
                        elif attractionFound:
                            attractionName = line[line.index("Name") + 6:].strip()
                            attractionFound = False
                    else:
                        if personName != "" and attractionName != "":
                            facts.append({
                                "Person": personName.strip(),
                                "Attraction": attractionName.strip(),
                                "Sentence": sentence.strip()
                            })
                        elif personName == "" and attractionName != "":
                            facts.append({
                                "Attraction": attractionName.strip(),
                                "Sentence": sentence.strip()
                            })
                        elif personName != "" and attractionName == "":
                            facts.append({
                                "Person": personName.strip(),
                                "Sentence": sentence.strip()
                            })
                        sentence = line
                        personName = ""
                        attractionName = ""
            if personName != "" and attractionName != "":
                facts.append({
                    "Person": personName.strip(),
                    "Attraction": attractionName.strip(),
                    "Sentence": sentence.strip()
                })
            elif personName == "" and attractionName != "":
                facts.append({
                    "Attraction": attractionName.strip(),
                    "Sentence": sentence.strip()
                })
            elif personName != "" and attractionName == "":
                facts.append({
                    "Person": personName.strip(),
                    "Sentence": sentence.strip()
                })

            # Сохраняем обработанные данные в БД
            coll = db.sorted_news
            for fact in facts:
                # print(fact)
                coll.insert_one(fact)
            facts.clear()
            curent += 1
            if counter == 0:
                break;
    except Exception as ex:
        print(ex)

    print("[INFO] Успех!")

if __name__=="__main__":
    main()