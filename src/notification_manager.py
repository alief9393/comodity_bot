# src/notification_manager.py

import telegram
import asyncio
import config

class NotificationManager:
    def __init__(self, token, chat_id):
        """
        Initializes the Telegram bot.
        
        Args:
            token (str): The Telegram bot token from BotFather.
            chat_id (str): The chat/channel ID to send messages to.
        """
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id
        print("NotificationManager initialized.")

    async def send_buy_signal(self, signal_details):
        """
        Formats and sends a buy signal notification to Telegram.
        
        Args:
            signal_details (dict): A dictionary containing all trade parameters.
        """
        symbol = signal_details['symbol']
        entry_price = signal_details['entry_price']
        stop_loss = signal_details['stop_loss']
        take_profit = signal_details['take_profit']
        reason = signal_details['reason']
        
        message = (
            f"🚨 **GOLD BUY SIGNAL** 🚨\n\n"
            f"**Symbol:** `{symbol}`\n"
            f"**Strategy:** `{reason}`\n\n"
            f"**Entry Price:** `{entry_price:.3f}`\n"
            f"**Stop Loss:** `{stop_loss:.3f}`\n"
            f"**Take Profit:** `{take_profit:.3f}`\n\n"
            f"Please verify on the chart before taking any action."
        )

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            print(f"Successfully sent signal notification to Telegram channel {self.chat_id}.")
        except Exception as e:
            print(f"Failed to send Telegram message. Error: {e}")

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    dummy_signal = {
        'symbol': 'XAUUSDm-TEST',
        'entry_price': 3800.500,
        'stop_loss': 3780.000,
        'take_profit': 3850.250,
        'reason': 'Test Signal'
    }

    test_token = os.getenv('TELEGRAM_BOT_TOKEN')
    test_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not test_token or not test_chat_id:
        print("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in the .env file to run the test.")
    else:
        notifier = NotificationManager(token=test_token, chat_id=test_chat_id)
        print("Sending a test message...")
        asyncio.run(notifier.send_buy_signal(dummy_signal))