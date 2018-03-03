"""
Wrapper around TelegramBot, with convenient behaviours
"""

from telegram import Bot as TelegramBot
from telegram import ParseMode
from telegram.ext import CommandHandler
from tabulate import tabulate
from .monitor import Monitor
from .network import Network
from .config import Config


class Bot:
    TELEGRAM_BOT = TelegramBot(Config.telegram_token())

    def __init__(self):
        self.monitors = {}

        self.commands = [
            # bot level
            CommandHandler("start", lambda *args: self.start(*args)),
            CommandHandler("stop", lambda *args: self.stop(*args)),
            # monitor level
            CommandHandler("all_stats", lambda *args: self.all_stats(*args)),
            CommandHandler("hashrates", lambda *args: self.hashrates(*args)),
            CommandHandler("gpu_temps", lambda *args: self.gpu_temps(*args)),
            CommandHandler("timestamp", lambda *args: self.timestamp(*args)),
        ]

    def send_table(self, chat_id, table):
        text = str(tabulate(table))
        self.send_message(text, chat_id, code=True)

    def send_message(self, text, chat_id, code=False):
        text = "```\n" + text + "\n```" if code else text
        Bot.TELEGRAM_BOT.send_message(
            text=text,
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN)

    def send_stats_for_chat(self, chat_id, included=[]):
        included = included or ["timestamp", "hashrate", "gpu_temps"]
        monitor = self.monitors.get(chat_id)
        if not monitor or not monitor.panels:
            error = "Get started by calling /start [panel_id]"
            return self.send_message(error, chat_id)

        monitor.send_stats(included)


    # actions

    def start(self, bot, update):
        cmd = update.effective_message.text.split(" ")
        if len(cmd) < 2 or len(cmd[1]) != 6:
            update.message.reply_text("please provide 6 character panel id")
            return

        chat_id = update.effective_chat.id
        if chat_id not in self.monitors:
            self.monitors[chat_id] = Monitor(chat_id, Network(), self)

        monitor = self.monitors[chat_id]
        monitor.panels.append(cmd[1])
        update.message.reply_text("Monitoring: " + repr(monitor.panels))

    def stop(self, bot, update):
        cmd = update.effective_message.text.split(" ")
        if len(cmd) < 2 or len(cmd[1]) != 6:
            update.message.reply_text("please provide 6 character panel id")
            return

        monitor = self.monitors[update.effective_chat.id]
        panel = cmd[1]
        if panel in monitor.panels:
            monitor.panels.remove(panel)
            update.message.reply_text("Stopped monitoring: " + panel)
        else:
            update.message.reply_text("Panel not found: " + repr(monitor.panels))

    def timestamp(self, bot, update):
        self.send_stats_for_chat(update.effective_chat.id, ["timestamp"])

    def hashrates(self, bot, update):
        self.send_stats_for_chat(update.effective_chat.id, ["hashrate"])

    def gpu_temps(self, bot, update):
        self.send_stats_for_chat(update.effective_chat.id, ["gpu_temps"])

    def all_stats(self, bot, update):
        self.send_stats_for_chat(update.effective_chat.id)

    # scheduler

    def update(self):
        for monitor in self.monitors.values():
            monitor.update()