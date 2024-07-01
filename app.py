from flask import Flask, render_template, request
from bs4 import  BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from flask_sqlalchemy import SQLAlchemy
from models import db, Product
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///searches_and_prices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
driver = webdriver.Chrome()

db.init_app(app)

def create_tables():
    with app.app_context():
        db.create_all()

def save_product(asin, prices):
    product = Product(
        asin=asin,
        price_us=prices[0]['price'],
        link_us=prices[0]['url'],
        price_uk=prices[1]['price'],
        link_uk=prices[1]['url'],
        price_de=prices[2]['price'],
        link_de=prices[2]['url'],
        price_ca=prices[3]['price'],
        link_ca=prices[3]['url']
    )
    db.session.add(product)
    db.session.commit()


def generateAsinUrl(country_code,asin):
    if country_code == 'us':
        url = f'https://www.amazon.com/dp/{asin}'
    elif country_code == 'uk':
            url = f'https://www.amazon.co.uk/dp/{asin}'
    elif country_code == 'de':
        url = f'https://www.amazon.de/dp/{asin}'
    elif country_code == 'ca':
        url = f'https://www.amazon.ca/dp/{asin}'
        
    return url

def initializeDriver(country_code,search=None,asin=None):
    if country_code == 'us':
            url = 'https://www.amazon.com'
            global driver
    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        if country_code == 'uk':
            url = 'https://www.amazon.co.uk'
        elif country_code == 'de':
            url = 'https://www.amazon.de'
        elif country_code == 'ca':
            url = 'https://www.amazon.ca'
        
    if search:
        url += f"/s?k={search}"
        
    elif asin:
        url += f"/dp/{asin}"
    driver.get(url)

    return driver

def filterItems(items):
    data = []
    for item in items:
        obj = {}
        
        name = item.find("span", {"class":"a-size-base-plus a-color-base a-text-normal"})
        image = item.find("img", {"class":"s-image"})
        p1 = item.find("span", {"class":"a-price-whole"})
        p2 = item.find("span", {"class":"a-price-fraction"})
        price = f"{p1}{p2}"
        asin = item.get("data-asin")       
        
        if name == None:
            name = item.find("span", {"class":"a-size-medium a-color-base a-text-normal"})
        if p1 == None or p2 == None:
            price = "Not Available"

        obj['name'] = name
        obj['image'] = image
        obj['price'] = price
        obj['asin'] = asin
        data.append(obj)

    return data

@app.route("/", methods = ["POST","GET"])
def home():
    if request.method == "POST":
        name = request.form["name"]
        name = name.replace(' ', '+')
        driver = initializeDriver(country_code="us", search=name)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.find_all("div", {"data-component-type":"s-search-result"}, limit=10)
        data = filterItems(items)

        return render_template("test.html", content = list(data))
    else:
        return render_template("root.html")

@app.route("/compare/<asin>")
def compareProducts(asin):
    prices = fetchComparisonData(asin)
    save_product(asin, prices)

    return render_template("comparison.html", prices=prices)

def scrapeForComparison(country_code,asin):
    driver = initializeDriver(country_code,asin=asin)
    url = generateAsinUrl(country_code,asin)
    obj = {"url":url, "price":getPrice(driver,country_code)}
    return obj


def fetchComparisonData(asin):
    codes = ['us', 'uk', 'de', 'ca']
    prices = []

    for country_code in codes:
        driver = initializeDriver(country_code,asin=asin)
        url = generateAsinUrl(country_code,asin)
        obj = {"url":url, "price":getPrice(driver,country_code)}
        prices.append(obj)

    return prices  

def getPrice(driver, country_code):
    match = False
    soup = BeautifulSoup(driver.page_source, "html.parser")
    availability = soup.find("span",{"class":"a-color-price"})
    if availability and "Currently unavailable" in availability.text:
        return "Not Available!"

    if country_code == 'de' or country_code == 'ca':
        item = soup.find_all("div", {"id":"ppd"}, limit=1)
        if item:
            current_elem = item[0]
            price_elem = current_elem.find_all("span", {"class":"a-offscreen"},limit=1)
        else:
            price_elem = None
    else:
        price_elem = soup.find_all("span", {"class":"a-offscreen"},limit=1)

    if price_elem:
        price = price_elem[0].text
        price = price.replace('\u200e','').replace('$','').replace('£','').replace('€','').replace(',','.')
    
        print(f"{country_code}, {price}")
        match = re.search(r'\d+\.\d+', price)

    if match:
        price = float(price)
        return fixCurrencyDifference(price,country_code)
    
    return "Not Available"

def fixCurrencyDifference(price, country_code):
    exchange_rates = { "uk": 1.26, "de": 1.09,  "ca": 0.73 }

    if price != "Not Available" and country_code in exchange_rates:
        price *= exchange_rates[country_code]

    return round(price,2)

@app.route('/history', methods=['GET'])
def history():
    products = Product.query.all()
    return render_template('history.html', products=products)

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)