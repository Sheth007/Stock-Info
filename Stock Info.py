import telebot
import requests
from bs4 import BeautifulSoup
import logging
import datetime

Token = "6960119409:AAGB6q3jMZNfpohyG4GQpxRuf4xQpv7orTc"  # Replace with your actual token
NewsApiKey = "82a9c9d22a1c404485906e480e7bb7b4"  # Replace with your actual News API key
bot = telebot.TeleBot(Token)

# Configure basic logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def google_search(stock_name):
    base_url = f'https://www.google.com/search?q={stock_name} share price'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(base_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            price_elements = soup.find_all('span', {'class': 'IsqQVc NprOob wT3VGc'})
            prices = [element.text.strip() for element in price_elements]

            inrusd_elements = soup.find_all('span', {'class': 'knFDje'})
            inrusd = [element.text.strip() for element in inrusd_elements]

            return prices, inrusd
        else:
            logger.error(f"Error fetching price: {response.status_code}")
            return None, None
    except Exception as e:
        logger.error(f"An error occurred during web scraping: {str(e)}")
        return None, None

def fetch_stock_news(stock_symbol):
    base_url = 'https://newsapi.org/v2/everything'
    params = {
        'apiKey': NewsApiKey,
        'q': stock_symbol,
        'sortBy': 'publishedAt',
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return articles
    else:
        logger.error(f"Error fetching news: {response.status_code}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to the Stock Price Bot! Enter the stock name to get its current price or use /news to fetch related news.")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, """
    /help -> This is just a simple bot that displays share prices
    /news <stock_name> -> Get news related to a stock
    """)

@bot.message_handler(commands=['get_price'])
def get_stock_price(message):
    try:
        command, stock_name = message.text.split(' ', 1)
        bot.reply_to(message, f"Searching for the current price of {stock_name}...")
        prices, inrusd = google_search(stock_name)

        if prices and inrusd:
            response = f"Current price of {stock_name} is:\n"
            for price, usd in zip(prices, inrusd):
                response += f"{price} {usd}\n"
        else:
            response = f"No stock prices found for {stock_name}."

        bot.reply_to(message, response)
    except ValueError:
        bot.reply_to(message, "Please provide a stock name after the /get_price command.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")


@bot.message_handler(commands=['news'])
def get_stock_news(message):
    try:
        command, stock_name = message.text.split(' ', 1)
        bot.reply_to(message, f"Fetching news related to {stock_name}...")
        
        # Calculate the date one week ago from the current date
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        formatted_date = one_week_ago.strftime('%Y-%m-%d')

        news_articles = fetch_stock_news(stock_name, formatted_date)

        if news_articles:
            response = f"News articles related to {stock_name} in the past week:\n"
            current_length = len(response)

            for index, article in enumerate(news_articles, start=1):
                article_text = f"{index}. {article['title']} - {article['url']}\n"
                article_length = len(article_text)

                # Check if adding the current article exceeds the message length limit
                if current_length + article_length <= 4096:
                    response += article_text
                    current_length += article_length
                else:
                    # If it exceeds the limit, send the current response and start a new one
                    bot.reply_to(message, response)
                    response = article_text
                    current_length = article_length

            # Send the remaining response, if any
            if response:
                bot.reply_to(message, response)
        else:
            response = f"No news articles found for {stock_name} in the past week."
            bot.reply_to(message, response)
    except ValueError:
        bot.reply_to(message, "Please provide a stock name after the /news command.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

def fetch_stock_news(stock_names, from_date):
    base_url = 'https://newsapi.org/v2/everything'
    
    # Use the stock names as keywords in the query
    query = ','.join(stock_names.split())

    params = {
        'apiKey': NewsApiKey,
        'q': query,
        'sortBy': 'publishedAt',
        'from': from_date,
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return articles
    else:
        logger.error(f"Error fetching news: {response.status_code}")
        return None



@bot.message_handler(func=lambda message: True)
def custom(message):
    try:
        stock_name = message.text
        bot.reply_to(message, f"Searching for the current price of {stock_name}...")
        prices, inrusd = google_search(stock_name)

        if prices and inrusd:
            response = f"Current price of {stock_name} is:\n"
            for price, usd in zip(prices, inrusd):
                response += f"{price} {usd}\n"
        else:
            response = f"No stock prices found for {stock_name}."

        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

bot.polling()
