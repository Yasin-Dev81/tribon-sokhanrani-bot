from persiantools.jdatetime import JalaliDateTime
from pyrogram import filters
import datetime
import psutil
import os

from config import TIME_ZONE, ADMINS_LIST_ID
from utils import generate_progress_bar


async def time(client, message):
    await message.reply_text(
        f"🔎 Time Zone: <spoiler>{TIME_ZONE}</spoiler>\n"
        f"⏳ Now DateTime: <i>{datetime.datetime.now(TIME_ZONE).strftime('%m/%d/%Y, %H:%M:%S')}</i>\n"
        f"- jalali DateTime: <i>{JalaliDateTime.now(TIME_ZONE)}</i>"
    )


async def sys(client, message):
    process = psutil.Process()

    # Memory usage
    mem = psutil.virtual_memory()
    total_ram = mem.total / (1024**3)  # Total RAM in GB
    used_ram = mem.used / (1024**3)  # Used RAM in GB
    available_ram = mem.available / (1024**3)
    memory_percent = process.memory_percent()  # Memory percent usage by this process

    # CPU usage
    cpu_percent = process.cpu_percent(interval=1)  # CPU usage over a 1-second interval
    cpu_count = psutil.cpu_count()

    await message.reply_text(
        f"Memory:\n{generate_progress_bar(memory_percent)}\n"
        f"<i>{used_ram:.1f}</i> GB of {total_ram:.1f} GB(free: {available_ram:.1f} GB)\n\n"
        f"CPU:\n{generate_progress_bar(cpu_percent)}\n"
        f"{cpu_percent:.1f}% of {cpu_count} cores"
    )


def register_system_handlers(app):
    app.on_message(filters.command("time"))(time)
    app.on_message(filters.command("sys") & filters.user(ADMINS_LIST_ID))(sys)
