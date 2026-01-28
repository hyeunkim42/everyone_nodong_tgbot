#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to handle '(my_)chat_member' updates.
Greets new users & keeps track of which chats the bot is in.

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os
from datetime import datetime

import dotenv
from telegram import LinkPreviewOptions, Update, Message
from telegram.error import BadRequest
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

GREET_DEBOUNCE_MESSAGE_COUNT = 3


class State:
    message_count: int
    last_message: Message | None

    def __init__(self):
        self.message_count = GREET_DEBOUNCE_MESSAGE_COUNT+1
        self.last_message = None


state = State()

WELCOME_MESSAGE_FORMAT = """
안녕하세요! 전국민주일반노조 누구나노조지회 채팅방에 오신것을 환영합니다!
조합비 납부 방법, 계좌번호 등 자주 묻는 질문은 홈페이지를 참조해주세요.
https://everyone-nodong.github.io/
최근 소식은 채팅방 상단 고정된 메시지에서 확인하실 수 있습니다.
""".strip()

RULES_MESSAGE_FORMAT = """
우리 모두가 지켜야 할 민주노총 평등수칙입니다.
평등수칙에 대한 자세한 내용은 <a href="https://nodong.org/data_paper/7814605">민주노총 평등수칙 해설서</a>를 참조해주세요.
""".strip()

QUESTION_MESSAGE_FORMAT = """
지회 운영에 대한 문의 사항이나 불편사항이 있으시다면 제작해둔 <a href="https://forms.gle/ivL5oGqwYV8TVyR76">구글폼</a>, 지회 텔레그램 방(전체, 권역별), 운영위원에게 직접 문의를 부탁드립니다.
"""

CALENDAR_MESSAGE_FORMAT = """
<a href="https://calendar.google.com/calendar/u/0/embed?src=b3c57107d44dd371af3df900c5fa541b603080a33702e1b20a9b85e1b38aef33@group.calendar.google.com&ctz=Asia/Seoul">달력 바로 보기</a>
"""

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()

    logger.info("message_count=%d <= GREET_DEBOUNCE_MESSAGE_COUNT=%d", state.message_count, GREET_DEBOUNCE_MESSAGE_COUNT)
    state.message_count += 1


async def greet_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("message_count=%d <= GREET_DEBOUNCE_MESSAGE_COUNT=%d", state.message_count, GREET_DEBOUNCE_MESSAGE_COUNT)

    if state.message_count <= GREET_DEBOUNCE_MESSAGE_COUNT:
        return

    state.message_count = 0

    if not update.effective_chat:
        return

    if state.last_message:
        try:
            await state.last_message.delete()
        except BadRequest:
            pass

    state.last_message = await update.effective_chat.send_message(
        text=WELCOME_MESSAGE_FORMAT,
        parse_mode=ParseMode.MARKDOWN,
        disable_notification=True,
    )


async def greet_message_force(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text=WELCOME_MESSAGE_FORMAT,
        parse_mode=ParseMode.MARKDOWN,
        disable_notification=True,
    )

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text=RULES_MESSAGE_FORMAT,
        parse_mode=ParseMode.HTML,
        disable_notification=True,
        link_preview_options=LinkPreviewOptions(
            url="https://everyone-nodong.github.io/assets/rule-of-equality.jpg",
            prefer_large_media=True,
            show_above_text=True,
        )
    )

async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text=QUESTION_MESSAGE_FORMAT,
        parse_mode=ParseMode.HTML,
        disable_notification=True,
        link_preview_options=LinkPreviewOptions(
            is_disabled=False,
            prefer_large_media=False
        )
    )

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text=CALENDAR_MESSAGE_FORMAT,
        parse_mode=ParseMode.HTML,
        disable_notification=True,
        link_preview_options=LinkPreviewOptions(
            is_disabled=False,
            prefer_large_media=False
        )
    )



def main() -> None:
    """Start the bot."""
    dotenv.load_dotenv('.env.local', override=True)

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv('TG_TOKEN', '')).build()

    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.CHAT, count_message), group=0)
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_message), group=1)

    application.add_handler(CommandHandler("about", greet_message_force), group=2)
    application.add_handler(CommandHandler("rules", rules), group=2)
    application.add_handler(CommandHandler("question", question), group=2)
    application.add_handler(CommandHandler("calendar", calendar), group=2)

    # Run the bot until the user presses Ctrl-C
    # We pass 'allowed_updates' handle *all* updates including `chat_member` updates
    # To reset this, simply pass `allowed_updates=[]`
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()