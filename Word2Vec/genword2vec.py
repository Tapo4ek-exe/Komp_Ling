from pyspark.sql import SparkSession
from pyspark.ml.feature import Tokenizer
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import CountVectorizer
from pyspark.ml.feature import IDF
from pyspark.ml.feature import Word2Vec
import pymongo
import re

spark = SparkSession\
    .builder\
    .appName("SimpleApplication")\
    .getOrCreate()

# Подготовка данных
client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.bwhk4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.V1News
coll = db.news
counter = -1
with open("news.txt", "w", encoding="utf-8") as file:
    for news in coll.find().sort("_id", pymongo.DESCENDING):
        counter -= 1
        content = news["Content"]
        content = re.sub(r'[^\w\s]+|[\d]+', r' ', content).strip()
        file.write(content + "\n")
        if counter == 0:
            break


# Построчная загрузка файла в RDD
input_file = spark.sparkContext.textFile('news.txt')

# print(input_file.collect())
prepared = input_file.map(lambda x: ([x]))
df = prepared.toDF()
prepared_df = df.selectExpr('_1 as text')

# Разбить на токены
tokenizer = Tokenizer(inputCol='text', outputCol='words')
words = tokenizer.transform(prepared_df)

# Удалить стоп-слова
stop_words = StopWordsRemover.loadDefaultStopWords('russian')
stop_words.append(r"")
remover = StopWordsRemover(inputCol='words', outputCol='filtered', stopWords=stop_words)
filtered = remover.transform(words)

# Вывести стоп-слова для русского языка
print(stop_words)

# Вывести таблицу filtered
filtered.show()

# Вывести столбец таблицы words с токенами до удаления стоп-слов
words.select('words').show(truncate=False, vertical=True)

# Вывести столбец "filtered" таблицы filtered с токенами после удаления стоп-слов
filtered.select('filtered').show(truncate=False, vertical=True)

# Посчитать значения TF
vectorizer = CountVectorizer(inputCol='filtered', outputCol='raw_features').fit(filtered)
featurized_data = vectorizer.transform(filtered)
featurized_data.cache()
vocabulary = vectorizer.vocabulary

# Вывести таблицу со значениями частоты встречаемости термов.
featurized_data.show()

# Вывести столбец "raw_features" таблицы featurized_data
featurized_data.select('raw_features').show(truncate=False, vertical=True)

# Вывести список термов в словаре
print(vocabulary)


# Посчитать значения DF
idf = IDF(inputCol='raw_features', outputCol='features')
idf_model = idf.fit(featurized_data)
rescaled_data = idf_model.transform(featurized_data)

# Вывести таблицу rescaled_data
rescaled_data.show()

# Вывести столбец "features" таблицы featurized_data
rescaled_data.select('features').show(truncate=False, vertical=True)

# Построить модель Word2Vec
word2Vec = Word2Vec(vectorSize=100, minCount=10, inputCol='filtered', outputCol='result')
model = word2Vec.fit(filtered)
w2v_df = model.transform(filtered)
w2v_df.show()

model.write().overwrite().save("model")

spark.stop()
