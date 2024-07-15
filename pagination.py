from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import PRACTICES_PER_PAGE


def get_paginated_keyboard(practices, page, callback, keyboard_callback):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = practices[start:end]

    keyboard = [[InlineKeyboardButton(title, callback_data=f"{keyboard_callback}_{practice_id}")]
                for practice_id, title in paginated_practices]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(InlineKeyboardButton("Previous", callback_data=f"{callback}_{page - 1}"))
    if end < len(practices):
        navigation_buttons.append(InlineKeyboardButton("Next", callback_data=f"{callback}_{page + 1}"))

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append([InlineKeyboardButton("Exit", callback_data="back_home")])

    return InlineKeyboardMarkup(keyboard)


def users_paginated_keyboard(users, page, callback, keyboard_callback):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [[InlineKeyboardButton(f"{i.name} - {i.phone_number} - {'*' if bool(i.chat_id) else 'N'}", callback_data=f"{keyboard_callback}_{i.id}")]
                for i in paginated_practices]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(InlineKeyboardButton("Previous", callback_data=f"{callback}_{page - 1}"))
    if end < len(users):
        navigation_buttons.append(InlineKeyboardButton("Next", callback_data=f"{callback}_{page + 1}"))

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append([InlineKeyboardButton("Exit", callback_data="back_home")])

    return InlineKeyboardMarkup(keyboard)


def teachers_paginated_keyboard(users, page, callback, keyboard_callback):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [[InlineKeyboardButton(f"{i.name} - {i.tell_id} - {'*' if bool(i.chat_id) else 'N'}", callback_data=f"{keyboard_callback}_{i.id}")]
                for i in paginated_practices]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(InlineKeyboardButton("Previous", callback_data=f"{callback}_{page - 1}"))
    if end < len(users):
        navigation_buttons.append(InlineKeyboardButton("Next", callback_data=f"{callback}_{page + 1}"))

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append([InlineKeyboardButton("Exit", callback_data="back_home")])

    return InlineKeyboardMarkup(keyboard)

def none_teacher_paginated_keyboard(users, page, callback, keyboard_callback):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [[InlineKeyboardButton(f"{i.id} - {i.name}", callback_data=f"{keyboard_callback}_{i.id}")]
                for i in paginated_practices]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(InlineKeyboardButton("Previous", callback_data=f"{callback}_{page - 1}"))
    if end < len(users):
        navigation_buttons.append(InlineKeyboardButton("Next", callback_data=f"{callback}_{page + 1}"))

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append([InlineKeyboardButton("Exit", callback_data="back_home")])

    return InlineKeyboardMarkup(keyboard)
