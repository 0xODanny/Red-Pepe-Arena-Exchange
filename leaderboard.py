import os
import telegram
from telegram.constants import ParseMode
from botutils import arena, sql
from dotenv import load_dotenv
import asyncio

load_dotenv()

PATH_TO_DB = os.environ['PATH_TO_DB']
BEARER_TOKEN = 'Bearer ' + os.environ['BEARER_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
DEV_NOTIFICATION_ID = os.environ['DEV_NOTIFICATION_ID']
CHAT_NOTIFICATION_ID = os.environ['CHAT_NOTIFICATION_ID']

async def notify_dev_leaderboard(message):
    message = message.replace('<br>','\n').replace('@','')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=DEV_NOTIFICATION_ID, text=message, parse_mode='html')

async def notify_tg_group_leaderboard(message):
    message = message.replace('<br>','\n').replace('@','')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_NOTIFICATION_ID, text=message, parse_mode='html')

def sort_json_by_value(object):
    try:
        return float(object['amt'])
    except KeyError:
        return 0

def sort_swappers_by_freq(object):
    try:
        return int(object['frequency'])
    except KeyError:
        return 0

conn = sql.create_connection(PATH_TO_DB)
sql.create_tables(conn)

all_txns = sql.get_txns(conn)

all_txns = [k for k in all_txns if k['amt'] != 'x']
if len(all_txns) < 3:
    print("Not enough transactions to process.")
    exit()
all_txns.sort(key=sort_json_by_value, reverse=True)
first = all_txns[0]
second = all_txns[1]
third = all_txns[2]

print(first, second, third)

total = 0.00
for txn in all_txns:
    total += float(txn['amt'])
print(total)

swappers = [k['user'] for k in all_txns]
swappers_dict = {i:swappers.count(i) for i in swappers}
print(swappers_dict)
swappers = []
for swapper in swappers_dict.keys():
    s = {}
    s['user'] = swapper
    s['frequency'] = swappers_dict[swapper]
    swappers.append(s)

swappers.sort(key=sort_swappers_by_freq, reverse=True)
print(swappers[0],swappers[1],swappers[2])
message = '<b>All Time Stats</b><br>Top 3 Largest Swaps:<br>1. %s AVAX by @%s<br>2. %s AVAX by @%s<br>3. %s AVAX by @%s<br><br>Total AVAX Swapped: %s' % (first['amt'], first['user'], second['amt'], second['user'], third['amt'], third['user'], total)
message += '<br><br>Top Swappers:<br>1. @%s with %s swaps<br>2. @%s with %s swaps<br>3. @%s with %s swaps' % (swappers[0]['user'], swappers[0]['frequency'], swappers[1]['user'], swappers[1]['frequency'], swappers[2]['user'], swappers[2]['frequency'])

# Run the async functions
asyncio.run(notify_dev_leaderboard(message))
asyncio.run(notify_tg_group_leaderboard(message))
arena.notify_arena_leaderboard(BEARER_TOKEN, message)
