from email.mime.image import MIMEImage
from nordpool import elspot
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dateutil import tz
from datetime import date, timedelta
from tabulate import tabulate
import matplotlib.pyplot as plt
from io import BytesIO
import yaml
import os
from dotenv import load_dotenv, find_dotenv

def generate_html_table(price_list: list, format: str, price_date: str):
    html_template = """
    <html><body>
    <h2>{title}</h2>
    <h4>{date}</h4>
    {table}
    </body></html>
    """
    return html_template.format(
        title=config['title'], 
        date=price_date, 
        table=tabulate(price_list, headers="keys", tablefmt=format, stralign="right", numalign="center", floatfmt=".6f")
    )


def sendEmail(subject:str, text: str, imageFile: BytesIO):
    message = MIMEMultipart("alternative", None, [MIMEText(text), MIMEText(text, 'html')])
    message['Subject'] = subject
    message['From'] = config['email']['from']
    message['To'] = config['email']['to']
    if config['email']['bcc']:
        message['Bcc'] = ', '.join(config['email']['bcc'])

    image = MIMEImage(imageFile.getvalue(), name='chart.png')
    message.attach(image)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(config['smtp']['server'], config['smtp']['port'], context=context) as server:
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.send_message(message)

def get_bar_color(price):
    if price > config['plot']['red_threshold']:
        return 'red'
    elif price > config['plot']['orange_threshold']:
        return 'orange'
    elif price > config['plot']['blue_threshold']:
        return 'blue'
    else:
        return 'green'

def plot(price_list: list, title):
    x = [x['Time'] for x in price_list]
    y = [x['Price, EUR/kwh'] for x in price_list]

    plt.figure(figsize=(config['plot']['width'], config['plot']['height']))
    plt.title(title)
    plt.xlabel(config['plot']['xlabel'])
    plt.ylabel(config['plot']['ylabel'])
    plt.grid(axis='y')
    
    bar_colors = [get_bar_color(x['Price, EUR/kwh']) for x in price_list]
    bars = plt.bar(x, y, label=x, width=0.8, align='center', color=bar_colors)
    plt.bar_label(bars, padding=10)
    
    image = BytesIO()
    plt.savefig(image, format='png')

    return image

# Read configs
config = yaml.safe_load(open("config.yaml", encoding='utf-8'))

# Load env variables
load_dotenv(find_dotenv())
SMTP_LOGIN = os.getenv('SMTP_LOGIN')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Initialize class for fetching Elspot prices
prices_spot = elspot.Prices()

# Fetch hourly Elspot prices
hourly_prices = prices_spot.hourly(areas=['LV'])

# Get date
price_date = hourly_prices["areas"]["LV"]["values"][0]['start'].astimezone(tz.gettz(config['time_zone'])).strftime("%d.%m.%Y")

# Set title
title = config['title'] + " " + price_date

# Initialize empty list
price_list = []

for i in range(24):
    time = hourly_prices["areas"]["LV"]["values"][i]['start']
    lv_price = hourly_prices["areas"]["LV"]["values"][i]['value'] # EUR/Mwh
    price_list.append({
        'Time' : time.astimezone(tz.gettz(config['time_zone'])).strftime("%H:00"),
        'Price, EUR/kwh' : lv_price / 1000 
    })

# Generate chart
image = plot(price_list, title)

# Create table
table = generate_html_table(price_list, "html", price_date)

# Send email
sendEmail(title, table, image)

# Debug
#print(generate_html_table(price_list, "simple", price_date))
