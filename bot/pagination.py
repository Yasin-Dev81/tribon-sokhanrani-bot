from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import PRACTICES_PER_PAGE


def get_paginated_keyboard(
    practices, page, callback, keyboard_callback, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = practices[start:end]

    keyboard = [
        [InlineKeyboardButton(i.title, callback_data=f"{keyboard_callback}_{i.id}")]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback}_{page - 1}")
        )
    if end < len(practices):
        navigation_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback}_{page + 1}")
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def select_teacher_paginated_keyboard(
    practices, page, callback, keyboard_callback, user_practice_id, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = practices[start:end]

    keyboard = [
        [InlineKeyboardButton(i.title, callback_data=f"{keyboard_callback}_{user_practice_id}_{i.id}")]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback}_{page - 1}")
        )
    if end < len(practices):
        navigation_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback}_{page + 1}")
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def users_paginated_keyboard(
    users, page, callback, keyboard_callback, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [
        [
            InlineKeyboardButton(
                f"{i.name} {'✅' if bool(i.chat_id) else '❎'}",
                callback_data=f"{keyboard_callback}_{i.id}",
            )
        ]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback}_{page - 1}")
        )
    if end < len(users):
        navigation_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback}_{page + 1}")
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def teachers_paginated_keyboard(
    users, page, callback, keyboard_callback, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [
        [
            InlineKeyboardButton(
                f"{i.name} {'✅' if bool(i.chat_id) else '❎'}",
                callback_data=f"{keyboard_callback}_{i.id}",
            )
        ]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback}_{page - 1}")
        )
    if end < len(users):
        navigation_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback}_{page + 1}")
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)

def poor_teachers_paginated_keyboard(
    users, page, callback, keyboard_callback, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [
        [
            InlineKeyboardButton(
                f"{i.name} | {i.correction_ratio:.0f}% | {i.not_corrected}",
                callback_data=f"{keyboard_callback}_{i.id}",
            )
        ]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback}_{page - 1}")
        )
    if end < len(users):
        navigation_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback}_{page + 1}")
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def none_teacher_paginated_keyboard(
    users, page, callback, keyboard_callback, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [
        [
            InlineKeyboardButton(
                f"{i.id} | {i.name}", callback_data=f"{keyboard_callback}_{i.id}"
            )
        ]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback}_{page - 1}")
        )
    if end < len(users):
        navigation_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback}_{page + 1}")
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def none_teacher_paginated_keyboard_t(
    users, page, callback, keyboard_callback, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = users[start:end]

    keyboard = [
        [
            InlineKeyboardButton(
                f"{i.id} | {i.user_id}", callback_data=f"{keyboard_callback}_{i.id}"
            )
        ]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback}_{page - 1}")
        )
    if end < len(users):
        navigation_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback}_{page + 1}")
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def user_practice_paginated_keyboard(
    practices, page, practice_id, callback, keyboard_callback, back_query="back_home"
):
    start = page * PRACTICES_PER_PAGE
    end = start + PRACTICES_PER_PAGE
    paginated_practices = practices[start:end]

    keyboard = [
        [InlineKeyboardButton(i.title, callback_data=f"{keyboard_callback}_{i.id}")]
        for i in paginated_practices
    ]

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                "◀️ Previous", callback_data=f"{callback}_{practice_id}_{page - 1}"
            )
        )
    if end < len(practices):
        navigation_buttons.append(
            InlineKeyboardButton(
                "Next ▶️", callback_data=f"{callback}_{practice_id}_{page + 1}"
            )
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    keyboard.append(
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=back_query),
            InlineKeyboardButton("exit!", callback_data="back_home"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)
