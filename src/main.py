import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time
import os
import asyncio

import config
from strategy import TradingStrategy
from notification_manager import NotificationManager

from dotenv import load_dotenv
load_dotenv()

mt5_account = int(os.getenv('MT5_ACCOUNT'))
mt5_password = os.getenv('MT5_PASSWORD')
mt5_server = os.getenv('MT5_SERVER')
mt5_path = os.getenv('MT5_PATH')

telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

def main():
    """
    The main function that runs the trading bot.
    """
    print("--- Commodity Bot Initializing ---")
    
    strategy = TradingStrategy()
    notifier = NotificationManager(token=telegram_token, chat_id=telegram_chat_id)

    print("Bot is now running. Waiting for the next check interval...")
    print(f"Check interval is set to {config.CHECK_INTERVAL_SECONDS / 60} minutes.")

    while True:
        try:
            if not mt5.initialize(path=mt5_path, login=mt5_account, password=mt5_password, server=mt5_server):
                print("initialize() failed, error code =", mt5.last_error())
                time.sleep(60)
                continue

            print(f"\n--- New Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            start_date = datetime(2023, 1, 1)
            end_date = datetime.now()
            
            df_h4 = pd.DataFrame(mt5.copy_rates_range(config.SYMBOL, mt5.TIMEFRAME_H4, start_date, end_date))
            df_h1 = pd.DataFrame(mt5.copy_rates_range(config.SYMBOL, mt5.TIMEFRAME_M30, start_date, end_date))
            
            if df_h4.empty or df_h1.empty:
                print("Failed to fetch data. Will retry on next interval.")
                mt5.shutdown()
                time.sleep(config.CHECK_INTERVAL_SECONDS)
                continue

            df_h4['time'] = pd.to_datetime(df_h4['time'], unit='s')
            df_h4.set_index('time', inplace=True)
            df_h1['time'] = pd.to_datetime(df_h1['time'], unit='s')
            df_h1.set_index('time', inplace=True)
            print(f"Data fetched successfully. H4 bars: {len(df_h4)}, H1 bars: {len(df_h1)}")

            df_h4, df_h1 = strategy.calculate_indicators(df_h4, df_h1)
            print("Indicators calculated.")

            signal = strategy.check_for_signal(df_h4, df_h1)

            if signal:
                print("\n✅✅✅ BUY SIGNAL GENERATED ✅✅✅")
                asyncio.run(notifier.send_buy_signal(signal))
            else:
                print("\n❌ No signal found. Conditions not met.")

            mt5.shutdown()
            print(f"Check complete. Sleeping for {config.CHECK_INTERVAL_SECONDS} seconds...")
            time.sleep(config.CHECK_INTERVAL_SECONDS)

        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            time.sleep(300) 

if __name__ == "__main__":
    main()