import logging
import concurrent.futures
import requests

from tradingview_ta import TA_Handler, Interval, Exchange

import asyncio
from telethon import TelegramClient, events


Log_Format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(filename = "log/log.log",
                    filemode = "a",
                    format = Log_Format, 
                    level = logging.INFO)

logger = logging.getLogger()

class TeleBot:
    api_id = 9462386
    api_hash = 'fd337743a6e6f42bf95890836a04a343'
    session_id = 'cryptoTA'
    client_id = 'cuaancrypto'    

    async def post_message(api_id, api_hash, session_id, client_id, message_list):
        client = TelegramClient(session_id, api_id, api_hash)
        for msg in message_list:
            await client.start()
            if msg:
                logger.info("post to telebot...")
                await client.send_message(client_id, msg)


class CryptoTA:

    screener = "CRYPTO"
    exchange = "BINANCE"
    interval_15M = Interval.INTERVAL_15_MINUTES
    indicator_15M = ['RSI7']
    oversold_15M = 20
    overbought_15M = 85

    def get_coin_list(path_file):
        coin_list = []
        with open(path_file) as f:
            lines = f.readlines()
            for line in lines:
                coin_list.append(line.strip())
        return coin_list

    def getAllRSI15M(coin, screener, exchange, interval, indicator, oversold_15M, overbought_15M):
        res = ""

        try :
            dataTA = TA_Handler(
                symbol=coin,
                screener=screener,
                exchange=exchange,
                interval=interval
            )

            rsi_data = dataTA.get_indicators(indicators=indicator)
            rsi_idx = rsi_data.get('RSI7')
            rsi_idx_fix = str(round(rsi_idx, 2))

            logger.info(coin +" : "+rsi_idx_fix)

            if rsi_idx >= overbought_15M:
                res += coin +" : "+rsi_idx_fix+" -> OVERBOUGHT\n"
            
            if rsi_idx <= oversold_15M:
                res += coin +" : "+rsi_idx_fix+" -> OVERSOLD\n"

        except Exception as err:
            logger.error(str(err) + " : "+coin)
        
        return res

    def getAllRSI15MParallel(coin_list, screener, exchange, interval, indicator, oversold_idx,overbought_idx):
        logger.info("========START GET RSI OVERSOLD / OVERBOUGHT=========")
        res = []
        message = ""

        with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
            futures = []
            for coin in coin_list:
                futures.append(executor.submit(CryptoTA.getAllRSI15M, coin, screener, exchange, interval, indicator, oversold_idx, overbought_idx))

            for future in concurrent.futures.as_completed(futures):
                try:
                    if len(message + future.result()) >= 4096:
                        res.append(message)
                        message = ""

                    message += future.result()
                except requests.ConnectTimeout:
                    logger.error("ConnectTimeout.")
            res.append(message)
        logger.info("========FINISH GET RSI OVERSOLD / OVERBOUGHT=========")
        return res


if __name__ == "__main__":
    coin_list = CryptoTA.get_coin_list("coin_list.txt")
    messageRSI15M = CryptoTA.getAllRSI15MParallel(coin_list, CryptoTA.screener, CryptoTA.exchange, CryptoTA.interval_15M, CryptoTA.indicator_15M, 
                                                    CryptoTA.oversold_15M, CryptoTA.overbought_15M)

    asyncio.run(TeleBot.post_message(TeleBot.api_id, TeleBot.api_hash, TeleBot.session_id, TeleBot.client_id, messageRSI15M))
