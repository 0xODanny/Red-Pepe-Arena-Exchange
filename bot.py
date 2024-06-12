import os
import asyncio
import time
import json
import telegram
from dotenv import load_dotenv
from AvalancheAPI import AvalancheAPI
from botutils import scan, arena, sql

load_dotenv()

PATH_TO_DB = os.environ['PATH_TO_DB']
SERVICE_FEE = float(os.environ['SERVICE_FEE'])
TOKEN_ADDRESS = os.environ['TOKEN_ADDRESS']
MY_WALLET = os.environ['MY_WALLET']
SNOWSCAN_API_KEY = os.environ['SNOWSCAN_API_KEY']
BEARER_TOKEN = 'Bearer ' + os.environ['BEARER_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
DEV_NOTIFICATION_ID = os.environ['DEV_NOTIFICATION_ID']
CHAT_NOTIFICATION_ID = os.environ['CHAT_NOTIFICATION_ID']
BUYS_ENABLED = True
TOKEN_DECIMALS = int(os.environ['TOKEN_DECIMALS'])
BASE_DECIMALS = 18

async def notify_dev(message):
    if message:
        text = '%s' % message
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=DEV_NOTIFICATION_ID, text=text)

async def notify_tg_group(message):
    if message:
        text = '%s' % message
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=CHAT_NOTIFICATION_ID, text=text)

def read_users_json():
    try:
        with open('users.json', 'r') as openfile:
            json_object = json.load(openfile)
        return json_object
    except json.JSONDecodeError as e:
        print(f"Error reading users.json: {e}")
        return {}

def get_username(conn, address):
    address = address.lower()
    username = sql.get_username_from_db(conn, address)
    if username:
        return username
    else:
        username = arena.get_username(address)
        if username:
            sql.add_username_to_db(conn, address, username)
        else:
            try:
                users = read_users_json()
                username = users.get(address.lower(), None)
            except:
                username = None

            if not username:
                username = address.lower()
                sql.add_username_to_db(conn, address, username)
        return username

async def perform_transfers():
    conn = sql.create_connection(PATH_TO_DB)
    sql.create_tables(conn)
    payables = sql.get_waiting_transfers(conn)
    print('transfers waiting to be sent:')
    print(json.dumps(payables, indent=4))
    if payables:
        avapi = AvalancheAPI()
        for xfer in payables:
            sql.update_transfer_to_pending(conn, xfer['hash'])

        for xfer in payables:
            print('attempting:')
            print(xfer)
            time.sleep(0.2)  # Handle rate limiting, allowing 5 calls per second
            try:
                transferTxn = avapi.transfer(TOKEN_ADDRESS, xfer['to'], xfer['amount'])
                print("Transfer response: ", transferTxn)  # Print raw response for debugging
                if transferTxn:
                    await notify_dev(f'transferred {xfer["amount_readable"]} RPEPE to {xfer["username"]} - hash: {scan.make_explorer_link(transferTxn)}')
                    sql.update_transaction_with_transfer_data(conn, xfer['hash'], transferTxn, xfer['amount_readable'])
                    print(f"Marked transfer {xfer['hash']} as completed in the database")
                    arena.notify_arena(BEARER_TOKEN, xfer['username'], xfer['incoming'], xfer['amount_readable'], xfer['hash'], transferTxn)
                else:
                    await notify_dev(f'transfer failed. retrying later. {xfer["username"]}, {xfer["amount_readable"]} RPEPE, wallet {xfer["to"]}')
                    sql.update_transfer_to_waiting(conn, xfer['hash'])
                time.sleep(0.2)  # Additional delay to handle rate limiting
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
                sql.update_transfer_to_waiting(conn, xfer['hash'])
            except Exception as e:
                print(f"Error during transfer: {e}")
                sql.update_transfer_to_waiting(conn, xfer['hash'])

async def perform_buys():
    try:
        payables = scan.get_transfers(SNOWSCAN_API_KEY, MY_WALLET)
        print("Received payables: ", payables)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from API response: {e}")
        return

    if payables:
        conn = sql.create_connection(PATH_TO_DB)
        avapi = AvalancheAPI()
        sql.create_tables(conn)

        print('payables count: ', len(payables))
        total_buy_amount = 0
        payables_considered = []
        for payable in payables:
            if not sql.check_transaction(conn, payable['hash']):  # Check if transaction is already processed
                total_buy_amount += int(payable['value'])
                username = get_username(conn, payable['from'])
                await notify_dev(f'got a transaction from {username} - {int(payable["value"]) / 10 ** BASE_DECIMALS} avax - hash: {scan.make_explorer_link(payable["hash"])}')
                sql.add_transaction(conn, payable['hash'], int(payable['value']) / 10 ** BASE_DECIMALS, username)
                payables_considered.append(payable)
            else:
                print(f"Transaction {payable['hash']} is already processed.")

        print("Total buy amount before fee reduction: ", total_buy_amount)

        if payables_considered:
            total_buy_amount_less_fee = int(total_buy_amount * (1 - SERVICE_FEE))
            print("Total buy amount after fee reduction: ", total_buy_amount_less_fee)

            amt = None
            buy_success = False
            buy_txn_id = None
            try:
                amt, buy_success, buy_txn_id = avapi.buy(TOKEN_ADDRESS, total_buy_amount_less_fee)
                print("amt: ", amt)
                print("buy_success: ", buy_success)
                print("buy_txn_id: ", buy_txn_id)
                buy_success = True
                msg = f'Batch Buy succeeded for {len(payables_considered)} incoming transactions.'
                print(msg)
                await notify_dev(msg)
            except Exception as e:
                print(f"Error during batch buy: {e}")
                for payable in payables_considered:
                    sql.remove_transaction(conn, payable['hash'])
                buy_success = False
                msg = f'Batch Buy failed for {len(payables_considered)} incoming transactions. They have been removed from the db and will be retried shortly.'
                print(msg)
                await notify_dev(msg)

            if buy_success:
                qty_purchased = (int(amt) * 0.99) / 10 ** TOKEN_DECIMALS
                for payable in payables_considered:
                    pct_to_send = float(payable['value']) / float(total_buy_amount)
                    owed = float(qty_purchased) * pct_to_send
                    sql.update_transaction_with_buy_data(conn, payable['hash'], int(payable['value']) / 10 ** BASE_DECIMALS, buy_txn_id, owed)
                    username = get_username(conn, payable['from'])
                    await notify_tg_group(f'{username} tipped {int(payable["value"]) / 10 ** BASE_DECIMALS} to redpepeexchange')
            else:
                for payable in payables_considered:
                    sql.remove_transaction(conn, payable['hash'])
                buy_success = False
                msg = f'Batch Buy appeared to succeed, but no success ticket was sent for {len(payables_considered)} incoming transactions. They have been removed from the db and will be retried shortly.'
                print(msg)
                await notify_dev(msg)

if __name__ == "__main__":
    asyncio.run(perform_buys())
    asyncio.run(perform_transfers())
