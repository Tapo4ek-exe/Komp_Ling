import pymongo as pymongo
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import twitter_samples, stopwords
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk import FreqDist, classify, NaiveBayesClassifier

import re, string, random

def remove_noise(tweet_tokens, stop_words = ()):

    cleaned_tokens = []

    for token, tag in pos_tag(tweet_tokens):
        token = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|'\
                       '(?:%[0-9a-fA-F][0-9a-fA-F]))+','', token)
        token = re.sub("(@[A-Za-z0-9_]+)","", token)

        if tag.startswith("NN"):
            pos = 'n'
        elif tag.startswith('VB'):
            pos = 'v'
        else:
            pos = 'a'

        lemmatizer = WordNetLemmatizer()
        token = lemmatizer.lemmatize(token, pos)

        if len(token) > 0 and token not in string.punctuation and token.lower() not in stop_words:
            cleaned_tokens.append(token.lower())
    return cleaned_tokens

def get_all_words(cleaned_tokens_list):
    for tokens in cleaned_tokens_list:
        for token in tokens:
            yield token

def get_tweets_for_model(cleaned_tokens_list):
    for tweet_tokens in cleaned_tokens_list:
        yield dict([token, True] for token in tweet_tokens)

if __name__ == "__main__":

    positive_tweets = twitter_samples.strings('positive_tweets.json')
    negative_tweets = twitter_samples.strings('negative_tweets.json')
    text = twitter_samples.strings('tweets.20150430-223406.json')
    tweet_tokens = twitter_samples.tokenized('positive_tweets.json')[0]

    stop_words = stopwords.words('russian')

    positive_tweet_tokens = twitter_samples.tokenized('positive_tweets.json')
    negative_tweet_tokens = twitter_samples.tokenized('negative_tweets.json')

    positive_cleaned_tokens_list = []
    negative_cleaned_tokens_list = []

    for tokens in positive_tweet_tokens:
        positive_cleaned_tokens_list.append(remove_noise(tokens, stop_words))

    for tokens in negative_tweet_tokens:
        negative_cleaned_tokens_list.append(remove_noise(tokens, stop_words))

    all_pos_words = get_all_words(positive_cleaned_tokens_list)

    freq_dist_pos = FreqDist(all_pos_words)
    print(freq_dist_pos.most_common(10))

    positive_tokens_for_model = get_tweets_for_model(positive_cleaned_tokens_list)
    negative_tokens_for_model = get_tweets_for_model(negative_cleaned_tokens_list)

    positive_dataset = [(tweet_dict, "Positive")
                         for tweet_dict in positive_tokens_for_model]

    negative_dataset = [(tweet_dict, "Negative")
                         for tweet_dict in negative_tokens_for_model]

    dataset = positive_dataset + negative_dataset

    random.shuffle(dataset)

    train_data = dataset[:7000]
    test_data = dataset[7000:]

    classifier = NaiveBayesClassifier.train(train_data)

    print("Accuracy is:", classify.accuracy(classifier, test_data))

    print(classifier.show_most_informative_features(10))

    # Оценка предложений из БД
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.bwhk4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = client.V1News
    coll = db.sorted_news
    newsCount = coll.count_documents({})
    current = 0     # номер текущего предложения
    counter = -1    # ограничитель кол-ва предложения для обработки
    for news in coll.find():
        counter -= 1
        current += 1
        print(f"[INFO] Обработка предложения {current} из {newsCount}")
        tweet = news["Sentence"]
        custom_tokens = []
        custom_tokens = remove_noise(word_tokenize(tweet))
        coll2 = db.news_rated
        person = ""
        attraction = ""
        try:
            person = news["Person"]
        except:
            person = ""
        try:
            attraction = news["Attraction"]
        except:
            attraction = ""
        if person != "" and attraction != "":       # есть и персона, и достопримечательность
            coll2.insert_one({
                "Person": person.strip(),
                "Attraction": attraction.strip(),
                "Sentence": tweet.strip(),
                "Rate": classifier.classify(dict([token, True] for token in custom_tokens))
            })
        elif person != "" and attraction == "":     # есть персона, но нет достопримечательности
            coll2.insert_one({
                "Person": person.strip(),
                "Sentence": tweet.strip(),
                "Rate": classifier.classify(dict([token, True] for token in custom_tokens))
            })
        elif person == "" and attraction != "":     # есть достопримечательность, но нет персоны
            coll2.insert_one({
                "Attraction": attraction.strip(),
                "Sentence": tweet.strip(),
                "Rate": classifier.classify(dict([token, True] for token in custom_tokens))
            })
        if counter == 0:
            break




