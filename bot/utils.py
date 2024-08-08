from pyrogram import filters
import datetime

from config import TIME_ZONE, INFO_MSG


def build_tree(data, indent=0, is_last=True):
    result = []
    indent_str = "  " * indent
    if indent > 0:
        indent_str = indent_str[:-2] + ("└ " if is_last else "├ ")

    for index, (key, value) in enumerate(data.items()):
        is_last_item = index == len(data) - 1
        if isinstance(value, dict):
            result.append(f"{indent_str}{key}:")
            new_indent_str = indent_str[:-2] + ("  " if is_last else "│ ")
            result.append(build_tree(value, indent + 1, is_last_item))
        else:
            prefix = indent_str[:-2] + ("└ " if is_last_item else "├ ")
            result.append(f"{prefix}{key}: {value}")
    return "\n".join(result)


async def time(client, message):
    await message.reply_text(
        f"🔎 Time Zone: <spoiler>{TIME_ZONE}</spoiler>\n"
        f"⏳ Now DateTime: <i>{datetime.datetime.now(TIME_ZONE).strftime('%m/%d/%Y, %H:%M:%S')}</i>"
    )


async def chat_id(client, message):
    data = message.chat.__dict__
    del data["photo"]
    await message.reply_text(build_tree(data))


async def info(client, message):
    await message.reply_text(INFO_MSG)


def register_utils_handlers(app):
    app.on_message(filters.command("time"))(time)
    app.on_message(filters.command("chat_id"))(chat_id)
    app.on_message(filters.regex("قوانین"))(info)
