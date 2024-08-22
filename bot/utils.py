from pyrogram import filters

from config import INFO_MSG


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


async def chat_id(client, message):
    data = message.chat.__dict__
    del data["photo"]
    await message.reply_text(build_tree(data))


async def info(client, message):
    await message.reply_text(INFO_MSG)


async def delete_this_msg(client, callback_query):
    await callback_query.answer("ok")
    await callback_query.message.delete()


async def namayeshi(client, callback_query):
    await callback_query.answer("این دکمه صرفا نمایشیه، کاربرد خاصی نداره")


def register_utils_handlers(app):
    app.on_message(filters.command("chat_id"))(chat_id)
    app.on_message(filters.regex("قوانین"))(info)
    app.on_callback_query(filters.regex("delete_this_msg"))(delete_this_msg)
    app.on_callback_query(filters.regex("namayeshi"))(namayeshi)
