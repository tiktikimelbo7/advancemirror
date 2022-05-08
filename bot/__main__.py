import signal
import os

from os import path as ospath, remove as osremove, execl as osexecl
from subprocess import run as srun
from asyncio import run as asyrun
from threading import Thread
from psutil import Process as psprocess
from time import time
from pyrogram import idle
from sys import executable
from telegram import ParseMode, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler
import time as taym
from wserver import start_server_async
from bot import HEROKU_API_KEY, HEROKU_APP_NAME, bot, app, dispatcher, updater, botStartTime, \
    IGNORE_PENDING_REQUESTS, IS_VPS, PORT, alive, web, a2c, \
    OWNER_ID, AUTHORIZED_CHATS, LOGGER, Interval, nox, rss_session, AUTO_DELETE_MESSAGE_DURATION
from .helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import auto_delete_message, sendMessage, sendMarkup, editMessage, sendLogFile
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, shell, eval, delete, \
    speedtest, count, leech_settings, search, rss, wayback, virustotal, hash, shortener, mediainfo, stats, antispam
try: import heroku3
except ModuleNotFoundError: srun("pip install heroku3", capture_output=False, shell=True)
try: import heroku3
except Exception as f:
    LOGGER.warning("heroku3 cannot imported. add to your deployer requirements.txt file.")
    LOGGER.warning(f)
    HEROKU_APP_NAME = None
    HEROKU_API_KEY = None

def start(update, context):
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f'''
This bot can mirror all your links to Google Drive.
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
        sendMarkup(start_string, context.bot, update, None)
    else:
        sendMarkup('Not authorized user.', context.bot, update, None)

def restart(update, context):
    cmd = update.effective_message.text.split(' ', 1)
    dynoRestart = False
    dynoKill = False
    if len(cmd) == 2:
        dynoRestart = (cmd[1].lower()).startswith('d')
        dynoKill = (cmd[1].lower()).startswith('k')
    if (not HEROKU_API_KEY) or (not HEROKU_APP_NAME):
        LOGGER.info("If you want Heroku features, fill HEROKU_APP_NAME HEROKU_API_KEY vars.")
        dynoRestart = False
        dynoKill = False
    if dynoRestart:
        LOGGER.info("Dyno Restarting.")
        restart_message = sendMessage("Dyno Restarting.", context.bot, update)
        with open(".restartmsg", "w") as f:
            f.truncate(0)
            f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
        heroku_conn = heroku3.from_key(HEROKU_API_KEY)
        app = heroku_conn.app(HEROKU_APP_NAME)
        app.restart()
    elif dynoKill:
        LOGGER.info("Killing Dyno. MUHAHAHA")
        sendMessage("Killed Dyno.", context.bot, update)
        heroku_conn = heroku3.from_key(HEROKU_API_KEY)
        app = heroku_conn.app(HEROKU_APP_NAME)
        proclist = app.process_formation()
        for po in proclist:
            app.process_formation()[po.type].scale(0)
    else:
        LOGGER.info("Normally Restarting.")
        restart_message = sendMessage("Normally Restarting.", context.bot, update)
        if Interval:
            Interval[0].cancel()
        alive.kill()
        procs = psprocess(web.pid)
        for proc in procs.children(recursive=True):
            proc.kill()
        procs.kill()
        clean_all()
        srun(["python3", "update.py"])
        nox.kill()
        a2cproc = psprocess(a2c.pid)
        for proc in a2cproc.children(recursive=True):
            proc.kill()
        a2cproc.kill()
        with open(".restartmsg", "w") as f:
            f.truncate(0)
            f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
        osexecl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)


help_string_telegraph = f'''<br>
<b>/{BotCommands.HelpCommand}</b>: To get this message
<br><br>
<b>/{BotCommands.MirrorCommand}</b> [download_url][magnet_link]: Start mirroring to Google Drive. Send <b>/{BotCommands.MirrorCommand}</b> for more help
<br><br>
<b>/{BotCommands.ZipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.UnzipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.QbMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start Mirroring using qBittorrent, Use <b>/{BotCommands.QbMirrorCommand} s</b> to select files before downloading
<br><br>
<b>/{BotCommands.QbZipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.QbUnzipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.LeechCommand}</b> [download_url][magnet_link]: Start leeching to Telegram, Use <b>/{BotCommands.LeechCommand} s</b> to select files before leeching
<br><br>
<b>/{BotCommands.ZipLeechCommand}</b> [download_url][magnet_link]: Start leeching to Telegram and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.UnzipLeechCommand}</b> [download_url][magnet_link][torent_file]: Start leeching to Telegram and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.QbLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent, Use <b>/{BotCommands.QbLeechCommand} s</b> to select files before leeching
<br><br>
<b>/{BotCommands.QbZipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.QbUnzipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.CloneCommand}</b> [drive_url][gdtot_url]: Copy file/folder to Google Drive
<br><br>
<b>/{BotCommands.CountCommand}</b> [drive_url][gdtot_url]: Count file/folder of Google Drive
<br><br>
<b>/{BotCommands.DeleteCommand}</b> [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo)
<br><br>
<b>/{BotCommands.WatchCommand}</b> [yt-dlp supported link]: Mirror yt-dlp supported link. Send <b>/{BotCommands.WatchCommand}</b> for more help
<br><br>
<b>/{BotCommands.ZipWatchCommand}</b> [yt-dlp supported link]: Mirror yt-dlp supported link as zip
<br><br>
<b>/{BotCommands.LeechWatchCommand}</b> [yt-dlp supported link]: Leech yt-dlp supported link
<br><br>
<b>/{BotCommands.LeechZipWatchCommand}</b> [yt-dlp supported link]: Leech yt-dlp supported link as zip
<br><br>
<b>/{BotCommands.LeechSetCommand}</b>: Leech settings
<br><br>
<b>/{BotCommands.SetThumbCommand}</b>: Reply photo to set it as Thumbnail
<br><br>
<b>/{BotCommands.RssListCommand}</b>: List all subscribed rss feed info
<br><br>
<b>/{BotCommands.RssGetCommand}</b>: [Title] [Number](last N links): Force fetch last N links
<br><br>
<b>/{BotCommands.RssSubCommand}</b>: [Title] [Rss Link] f: [filter]: Subscribe new rss feed
<br><br>
<b>/{BotCommands.RssUnSubCommand}</b>: [Title]: Unubscribe rss feed by title
<br><br>
<b>/{BotCommands.RssUnSubAllCommand}</b>: Remove all rss feed subscriptions
<br><br>
<b>/{BotCommands.CancelMirror}</b>: Reply to the message by which the download was initiated and that download will be cancelled
<br><br>
<b>/{BotCommands.CancelAllCommand}</b>: Cancel all downloading tasks
<br><br>
<b>/{BotCommands.ListCommand}</b> [query]: Search in Google Drive(s)
<br><br>
<b>/{BotCommands.SearchCommand}</b> [query]: Search for torrents with API
<br>sites: <code>rarbg, 1337x, yts, etzv, tgx, torlock, piratebay, nyaasi, ettv</code><br><br>
<b>/{BotCommands.StatusCommand}</b>: Shows a status of all the downloads
<br><br>
<b>/{BotCommands.RestartCommand}</b>: Restart bot. Use <b>/{BotCommands.RestartCommand} dyno</b> for dyno restarting. Use <b>/{BotCommands.RestartCommand} kill</b> to kill dyno.
<br><br>
<b>/{BotCommands.StatsCommand}</b>: Show Stats of the machine the bot is hosted on
<br><br>
<b>/{BotCommands.WayBackCommand}</b>: Archive a webpage with Wayback Machine
<br><br>
<b>/{BotCommands.VirusTotalCommand}</b>: Reply a file to scan with VirusTotal
<br><br>
<b>/{BotCommands.HashCommand}</b>: Reply a file to generate hash MD5, SHA1 etc.
<br><br>
<b>/{BotCommands.ShortenerCommand}</b>: Reply a link to short it.
<br><br>
<b>/{BotCommands.MediaInfoCommand}</b>: Reply a file to get mediainfo.
'''

help = telegraph.create_page(
    title='Bot Help',
    content=help_string_telegraph)["path"]

def bot_help(update, context):
    button = ButtonMaker()
    button.buildbutton("Click and Read", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(f'<a href="https://telegra.ph/{help}">Click and Read</a>', context.bot, update, reply_markup)

botcmds = [
        (f'{BotCommands.MediaInfoCommand}','media info'),
        (f'{BotCommands.SpeedCommand}','Speed of the bot'),
        (f'{BotCommands.StartCommand}','Start the bot'),
        (f'{BotCommands.MirrorCommand}','Mirror'),
        (f'{BotCommands.ZipMirrorCommand}','Mirror and upload as zip'),
        (f'{BotCommands.UnzipMirrorCommand}','Mirror and extract files'),
        (f'{BotCommands.QbMirrorCommand}','Mirror torrent using qBittorrent'),
        (f'{BotCommands.QbZipMirrorCommand}','Mirror torrent and upload as zip using qb'),
        (f'{BotCommands.QbUnzipMirrorCommand}','Mirror torrent and extract files using qb'),
        (f'{BotCommands.WatchCommand}','Mirror yt-dlp supported link'),
        (f'{BotCommands.ZipWatchCommand}','Mirror yt-dlp supported link as zip'),
        (f'{BotCommands.CloneCommand}','Copy file/folder to Drive'),
        (f'{BotCommands.LeechCommand}','Leech'),
        (f'{BotCommands.ZipLeechCommand}','Leech and upload as zip'),
        (f'{BotCommands.UnzipLeechCommand}','Leech and extract files'),
        (f'{BotCommands.QbLeechCommand}','Leech torrent using qBittorrent'),
        (f'{BotCommands.QbZipLeechCommand}','Leech torrent and upload as zip using qb'),
        (f'{BotCommands.QbUnzipLeechCommand}','Leech torrent and extract using qb'),
        (f'{BotCommands.LeechWatchCommand}','Leech yt-dlp supported link'),
        (f'{BotCommands.LeechZipWatchCommand}','Leech yt-dlp supported link as zip'),
        (f'{BotCommands.CountCommand}','Count file/folder of Drive'),
        (f'{BotCommands.DeleteCommand}','Delete file/folder from Drive'),
        (f'{BotCommands.CancelMirror}','Cancel a task'),
        (f'{BotCommands.CancelAllCommand}','Cancel all downloading tasks'),
        (f'{BotCommands.ListCommand}','Search in Drive'),
        (f'{BotCommands.LeechSetCommand}','Leech settings'),
        (f'{BotCommands.SetThumbCommand}','Set thumbnail'),
        (f'{BotCommands.StatusCommand}','Get mirror status message'),
        (f'{BotCommands.StatsCommand}','Bot usage stats'),
        (f'{BotCommands.PingCommand}','Ping the bot'),
        (f'{BotCommands.RestartCommand}','Restart the bot'),
        (f'{BotCommands.LogCommand}','Get the bot Log'),
        (f'{BotCommands.HelpCommand}','Get detailed help')
    ]

def main():
    bot.set_my_commands(botcmds)
    start_cleanup()
    if IS_VPS:
        asyrun(start_server_async(PORT))
    # Check if the bot is restarting
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f: chat_id, msg_id = map(int, f)
        try: bot.edit_message_text("Restarted successfully.", chat_id, msg_id)
        except Exception as e: LOGGER.error(e)
        osremove(".restartmsg")
    elif OWNER_ID:
        try:
            text = "<b>Bot Restarted.</b>"
            todel = bot.sendMessage(chat_id=OWNER_ID, text=text, parse_mode=ParseMode.HTML)
            Thread(target=auto_delete_message, args=(bot, todel)).start()
            if AUTHORIZED_CHATS:
                for i in AUTHORIZED_CHATS:
                    todel = bot.sendMessage(chat_id=i, text=text, parse_mode=ParseMode.HTML)
                    Thread(target=auto_delete_message, args=(bot, todel)).start()
        except Exception as e:
            LOGGER.warning(e)

    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS, allowed_updates=Update.ALL_TYPES)
    LOGGER.info("Bot Started.")
    signal.signal(signal.SIGINT, exit_clean_up)
    if rss_session is not None:
        rss_session.start()

app.start()
main()
idle()
