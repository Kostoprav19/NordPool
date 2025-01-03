from nordpool import elspot
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dateutil import tz
from tabulate import tabulate
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
        table=tabulate(price_list, headers="keys", tablefmt=format, stralign="right", numalign="center", floatfmt=config['float_format'])
    )


def sendEmail(subject: str, text: str):
    message = MIMEMultipart("alternative", None, [MIMEText(text), MIMEText(text, 'html')])
    message['Subject'] = subject
    message['From'] = config['email']['from']
    message['To'] = config['email']['to']
    if config['email']['bcc']:
        message['Bcc'] = ', '.join(config['email']['bcc'])

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


# Read configs
config = yaml.safe_load(open("config.yaml", encoding='utf-8'))

# Load env variables
load_dotenv(find_dotenv())
SMTP_LOGIN = os.getenv('SMTP_LOGIN')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
DEBUG = os.getenv('NORDPOOL_DEBUG')

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
    lv_price = hourly_prices["areas"]["LV"]["values"][i]['value']  # EUR/Mwh
    price_list.append({
        'Time': time.astimezone(tz.gettz(config['time_zone'])).strftime("%H:00"),
        'Price, cents/kwh': lv_price / 10
    })

# Create table
table = generate_html_table(price_list, "html", price_date)

# Send email
sendEmail(title, table)

# Debug
if DEBUG:
    print(generate_html_table(price_list, "simple", price_date))
