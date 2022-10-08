from email.mime.image import MIMEImage
from nordpool import elspot  # , elbas
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

# On Synology
#  python3 -m pip install nordpool
#  pip install -r requirements.txt

def formatTable(myList, format):
    html = """
    <html><body>
    <p>Nordpool Day-ahead prices:</p>
    {table}
    <br>
    Chart is attached to this email.
    </body></html>
    """
    html = html.format(
        table=tabulate(myList, headers="keys", tablefmt=format, stralign="right", numalign="decimal", floatfmt=".2f")
    )
    return html


def sendEmail(text, imageFile):
    message = MIMEMultipart("alternative", None, [MIMEText(text), MIMEText(text, 'html')])
    message['Subject'] = "Nordpool Day-ahead prices for " + (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
    message['From'] = config['email']['from']
    message['To'] = config['email']['to']
    #    message['Bcc'] = ', '.join(config['email']['bcc'])

    image = MIMEImage(imageFile.getvalue(), name='chart.png')
    message.attach(image)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(config['smtp']['server'], config['smtp']['port'], context=context) as server:
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.send_message(message)


def plot(mylist):
    x = [x['start'] for x in mylist]
    y = [x['price_kwh'] for x in mylist]

    plt.figure(figsize=(config['plot']['width'], config['plot']['height']))
    plt.title(config['plot']['title'])
    plt.xlabel(config['plot']['xlabel'])
    plt.ylabel(config['plot']['ylabel'])
    plt.grid(axis='y')
    bar_colors = ['red' if x['price_kwh'] > config['plot']['red_threshold'] else 'orange' if x['price_kwh'] > config['plot']['orange_threshold'] else 'blue' if x['price_kwh'] > config['plot']['blue_threshold'] else 'green' for x in mylist]
    bars = plt.bar(x, y, label=x, width=0.8, align='center', color=bar_colors)
    plt.bar_label(bars, padding=10)
    image = BytesIO()
    plt.savefig(image, format='png')

    return image

# Read configs
config = yaml.safe_load(open("config.yml", encoding='utf-8'))

# Load env variables
load_dotenv(find_dotenv())
SMTP_LOGIN = os.getenv('SMTP_LOGIN')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Initialize class for fetching Elspot prices
prices_spot = elspot.Prices()

# Fetch hourly Elspot prices for Finland and print the resulting dictionary
hourly = prices_spot.hourly(areas=['LV', 'FI'])

# Set a fixed component in tariff "Somijas", EUR/MWh
f = 48.86

# Generate empty list
mylist = [{} for sub in range(24)]

# Fill list with data
for i in range(24):
    time = hourly["areas"]["LV"]["values"][i]['start']
    mylist[i]['date'] = time.astimezone(tz.gettz('Europe/Riga')).strftime("%d.%m.%Y")
    mylist[i]['start'] = time.astimezone(tz.gettz('Europe/Riga')).strftime("%H:00")
    time = hourly["areas"]["LV"]["values"][i]['end']
    mylist[i]['end'] = time.astimezone(tz.gettz('Europe/Riga')).strftime("%H:00")
    mylist[i]['LV'] = hourly["areas"]["LV"]["values"][i]['value']
    mylist[i]['FI'] = hourly["areas"]["FI"]["values"][i]['value']
    mylist[i]['diff'] = abs(mylist[i]['LV'] - mylist[i]['FI'])
    mylist[i]['price_mwh'] = mylist[i]['diff'] + f
    mylist[i]['price_kwh'] = round(mylist[i]['price_mwh'] / 1000, 2)

# Generate chart
image = plot(mylist)

# Create table
table = formatTable(mylist, "html")

# Send email
sendEmail(table, image)

# Debug
# print(formatTable(mylist, "simple"))
