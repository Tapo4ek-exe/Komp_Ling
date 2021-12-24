import pymongo


client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.bwhk4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.V1News
coll = db.news_rated


obj_to_rate = input("Введите имя и фамилию персоны или название достопримечательности: ")
type = int(input("Выберите вариант: рейтинг для персоны - 1, рейтинг для достопримечательности - 2: "))
pos = 0     # кол-во позитивных оценок
neg = 0     # кол-во негативных оценок

# Подсчет позитивных и негативных оценок
if type == 1:
    for person in coll.find({"Person": obj_to_rate.strip()}):
        if person["Rate"].find("Pos") != -1:
            pos += 1
        else:
            neg += 1
else:
    for attraction in coll.find({"Attraction": obj_to_rate}):
        if attraction["Rate"].find("Pos") != -1:
            pos += 1
        else:
            neg += 1

# Вывод рейтинга
print(f"Рейтинг для '{obj_to_rate}':")
print(f"Кол-во позитиивных оценок - {pos}")
print(f"Кол-во негативных оценок - {neg}")
if pos != 0 or neg != 0:
    print(f"Соотношение позитивных оценок к негативным - {float(pos/(pos+neg)*100):.2f}% : {float(neg/(pos+neg)*100):.2f}%")


