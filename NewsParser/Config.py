MONGO = "mongodb+srv://admin:admin@cluster0.bwhk4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

URL = "http://v1.ru/text/"
HEADERS = {
    "Accept": "text / html, application / xhtml + xml, application / xml; q = 0.9, image / avif, image / webp, * / *;q = 0.8",
    "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64; rv: 94.0) Gecko / 20100101 Firefox / 94.0"
}

PATH = "News"           # папка для сохранения файлов со статьями
FILENAME = "news.csv"   # файл с последними сохраненными данными

ID = 1
SAVE_EVERY = 1          # промежуток сохранения файлов

START = 1       # номер страницы, которой начинается парсинг
END = 0         # номер страницы, до какой должен закончиться парсинг (0 - парсинг всех страниц)

soupSources = [
    {
        "PaginationBar": "HRahz PZm3",
        "Pages": "HRah1",
        "Articles": "IJamp",
        "Heading": "IJm9",
        "Description": "IJal3",
        "Date": "IJain IJam-",
        "Link": "IJm9",
        "ContentAll": "I5pv",
        "ContentPar": "INant",
        "Stats": "H3gt"
    },
    {
        "PaginationBar": "H3anl IXet",
        "Pages": "H3ann",
        "Articles": "G1ahf",
        "Heading": "G1ez",
        "Description": "G1afv",
        "Date": "G1ac3 G1ahz",
        "ContentAll": "J3el",
        "ContentPar": "G7aij",
        "Stats": "GLdh"
    },
    {
        "PaginationBar": "H1am- IXkb",
        "Pages": "H1anb",
        "Articles": "G-akz",
        "Heading": "G-kh",
        "Description": "G-akb",
        "Date": "G-all G-alh",
        "ContentAll": "J9ab9",
        "ContentPar": "G5aj3",
        "Stats": "GNgn"
    },
    {
        "PaginationBar": "G3akz L1xv",
        "Pages": "G3ak1",
        "Articles": "CRt3",
        "Heading": "CRil",
        "Description": "CRud",
        "Date": "CRu1 CRux",
        "ContentAll": "J5nb",
        "ContentPar": "B3qv",
        "Stats": "B5gb"
    },
    {
        "PaginationBar": "G9ak9 PBx5",
        "Pages": "G9ak-",
        "Articles": "CRt3",
        "Heading": "CRkp",
        "Description": "CRud",
        "Date": "CRu1 CRux",
        "ContentAll": "J7nv",
        "ContentPar": "BPoz",
        "Stats": "B5cd"
    }
]