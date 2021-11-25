import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from strings import Strings
from states import States


def handle_start(update: Update, _: CallbackContext):
    update.effective_message.reply_text(Strings.START)


def handle_help(update: Update, _: CallbackContext):
    update.effective_message.reply_text(Strings.HELP)


def handle_add(update: Update, _: CallbackContext):
    update.effective_message.reply_text(Strings.ASK_PHOTO)
    return States.WAITING_PHOTO


def handle_cancel(update: Update, _: CallbackContext):
    update.effective_message.reply_text(Strings.CANCEL)
    return ConversationHandler.END


def handle_new_photo(update: Update, callback_context: CallbackContext):
    if "photos" not in callback_context.user_data.keys():
        callback_context.user_data["photos"] = {}
    if update.effective_message.caption is None:
        callback_context.user_data["temporary"] = update.message.photo[-1].file_id
        update.effective_message.reply_text(Strings.EMPTY_NAME)
        return States.WAITING_NAME
    elif update.effective_message.caption in callback_context.user_data["photos"].keys():
        callback_context.user_data["temporary"] = update.message.photo[-1].file_id
        update.effective_message.reply_text(Strings.OLD_NAME)
        return States.WAITING_NAME

    update.effective_message.reply_text(Strings.GOT_PHOTO)
    callback_context.user_data["photos"][update.effective_message.caption] = update.message.photo[-1].file_id
    return States.WAITING_PHOTO


def handle_name(update: Update, callback_context: CallbackContext):
    if update.effective_message.text in callback_context.user_data["photos"].keys():
        update.effective_message.reply_text(Strings.OLD_NAME)
        return States.WAITING_NAME
    if "photos" not in callback_context.user_data.keys():
        callback_context.user_data["photos"] = {}
    callback_context.user_data["photos"][update.effective_message.text] = callback_context.user_data["temporary"]
    update.effective_message.reply_text(Strings.GOT_NAME)
    return States.WAITING_PHOTO


def handle_cancel_photo(update: Update, _: CallbackContext):
    update.effective_message.reply_text(Strings.CANCEL_PHOTO)
    return States.WAITING_PHOTO


def make_quiz_keyboard(right_name: str, data: dict, is_new_question: bool):
    if is_new_question:
        names = list(data["photos"].keys())
        data["questions_asked"] += 1
        data["user_answers"].append(None)
        data["list_not_asked_questions"].remove(right_name)
        sample_names = random.sample(names, min(len(names) - 1, 3))
        if right_name not in sample_names:
            sample_names.append(right_name)
        else:
            name = random.choice(names)
            while name in sample_names:
                name = random.choice(names)
            sample_names.append(name)
        random.shuffle(sample_names)

        data["questions"].append((right_name, sample_names))
    else:
        sample_names = data["questions"][data["question_id"]][1]
    buttons = []
    for i, name in enumerate(sample_names):
        if not is_new_question and data["user_answers"][data["question_id"]] == name:
            buttons.append([InlineKeyboardButton(f"✅ {name}", callback_data=f"{i}_PICK")])
        else:
            buttons.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"{i}_PICK")])

    prev_button = InlineKeyboardButton(Strings.PREV, callback_data="PREV")
    next_button = InlineKeyboardButton(Strings.NEXT, callback_data="NEXT")
    finish_button = InlineKeyboardButton(Strings.FINISH, callback_data="FINISH")

    if data["question_id"] == data["total_questions"] - 1:
        if data["question_id"] != 0:
            buttons.append([prev_button, finish_button])
        else:
            buttons.append([finish_button])
    elif data["question_id"] != 0:
        buttons.append([prev_button, next_button])
        buttons.append([InlineKeyboardButton(Strings.CANCEL_QUIZ, callback_data="CANCEL")])
    else:
        buttons.append([next_button])
        buttons.append([InlineKeyboardButton(Strings.CANCEL_QUIZ, callback_data="CANCEL")])

    return InlineKeyboardMarkup(buttons)


def handle_start_quiz(update: Update, callback_context: CallbackContext):
    if "photos" in callback_context.user_data.keys():
        right_name = random.choice(list(callback_context.user_data["photos"].keys()))

        callback_context.user_data["questions"] = []
        callback_context.user_data["question_id"] = 0
        callback_context.user_data["questions_asked"] = 0
        callback_context.user_data["list_not_asked_questions"] = list(callback_context.user_data["photos"].keys())
        callback_context.user_data["total_questions"] = min(10, len(callback_context.user_data["photos"]))
        callback_context.user_data["user_answers"] = []

        update.effective_message.reply_photo(
            callback_context.user_data["photos"][right_name],
            reply_markup=make_quiz_keyboard(right_name, callback_context.user_data, True)
        )
        return States.WAITING_ANSWER

    update.effective_message.reply_text(Strings.EMPTY_LIST)


def handle_prev_question(update: Update, callback_context: CallbackContext):
    update.callback_query.answer()
    right_name = callback_context.user_data["questions"][callback_context.user_data["question_id"] - 1][0]

    callback_context.user_data["question_id"] -= 1
    update.callback_query.message.edit_media(
        InputMediaPhoto(
            callback_context.user_data["photos"][right_name]
        ),
        reply_markup=make_quiz_keyboard(
            right_name,
            callback_context.user_data,
            False
        ))


def handle_next_question(update: Update, callback_context: CallbackContext):
    if callback_context.user_data["user_answers"][callback_context.user_data["question_id"]] is None:
        update.callback_query.answer(Strings.SELECT, show_alert=True)
        return

    update.callback_query.answer()
    if callback_context.user_data["question_id"] == callback_context.user_data["questions_asked"] - 1:
        right_name = random.choice(callback_context.user_data["list_not_asked_questions"])
    else:
        right_name = callback_context.user_data["questions"][callback_context.user_data["question_id"] + 1][0]

    callback_context.user_data["question_id"] += 1
    update.callback_query.message.edit_media(InputMediaPhoto(
        callback_context.user_data["photos"][right_name]
    ),
        reply_markup=make_quiz_keyboard(
            right_name,
            callback_context.user_data,
            callback_context.user_data["question_id"] ==
            callback_context.user_data[
                "questions_asked"]
        ))


def handle_finish_quiz(update: Update, callback_context: CallbackContext):
    if callback_context.user_data["user_answers"][callback_context.user_data["question_id"]] is None:
        update.callback_query.answer(Strings.SELECT, show_alert=True)
        return

    update.effective_message.delete()
    right_answer = 0
    for current_answer, current_right_answer in zip(callback_context.user_data["user_answers"],
                                                    callback_context.user_data["questions"]):
        if current_answer == current_right_answer[0]:
            right_answer += 1

    result = right_answer / callback_context.user_data['questions_asked']
    if result <= 0.4:
        quality = Strings.BAD_RESULT
    elif result <= 0.8:
        quality = Strings.GOOD_RESULT
    else:
        quality = Strings.SUPER_RESULT

    format_result = format(result * 100, ".2f")
    update.effective_message.reply_text(f"{Strings.RESULT}{format_result}%\n\n{quality}")
    return ConversationHandler.END


def handle_person_choice(update: Update, callback_context: CallbackContext):
    update.callback_query.answer()
    current_answer = callback_context.user_data["questions"][callback_context.user_data["question_id"]][1][
        int(update.callback_query.data[:-5])]
    callback_context.user_data["user_answers"][
        callback_context.user_data["question_id"]] = current_answer

    update.effective_message.edit_reply_markup(reply_markup=make_quiz_keyboard(
        callback_context.user_data["questions"][callback_context.user_data["question_id"]][0],
        callback_context.user_data, False
    ))


def make_collection_keyboard(data: dict):
    buttons = []
    prev_button = InlineKeyboardButton(Strings.PREV, callback_data="PREV")
    next_button = InlineKeyboardButton(Strings.NEXT, callback_data="NEXT")
    finish_button = InlineKeyboardButton(Strings.END_GET, callback_data="FINISH")
    if data["photo_id"] == len(data["photos"]) - 1:
        if data["photo_id"] != 0:
            buttons.append([prev_button, finish_button])
        else:
            buttons.append([finish_button])
    elif data["photo_id"] != 0:
        buttons.append([prev_button, next_button])
        buttons.append([InlineKeyboardButton(Strings.END_GET, callback_data="CANCEL")])
    else:
        buttons.append([next_button])
        buttons.append([InlineKeyboardButton(Strings.END_GET, callback_data="CANCEL")])

    return InlineKeyboardMarkup(buttons)


def handle_start_get_collection(update: Update, callback_context: CallbackContext):
    if "photos" in callback_context.user_data.keys():
        callback_context.user_data["photo_id"] = 0
        update.effective_message.reply_photo(
            callback_context.user_data["photos"][list(callback_context.user_data["photos"].keys())[0]],
            caption=list(callback_context.user_data["photos"].keys())[0],
            reply_markup=make_collection_keyboard(callback_context.user_data)
        )
        return States.WAITING_TRANSITION

    update.effective_message.reply_text(Strings.EMPTY_LIST)


def handle_prev_photo(update: Update, callback_context: CallbackContext):
    update.callback_query.answer()
    callback_context.user_data["photo_id"] -= 1
    update.callback_query.message.edit_media(
        InputMediaPhoto(
            callback_context.user_data["photos"][
                list(callback_context.user_data["photos"].keys())[callback_context.user_data["photo_id"]]]
        ),
    )

    update.effective_message.edit_caption(
        list(callback_context.user_data["photos"].keys())[callback_context.user_data["photo_id"]],
        reply_markup=make_collection_keyboard(callback_context.user_data)
    )


def handle_next_photo(update: Update, callback_context: CallbackContext):
    update.callback_query.answer()
    callback_context.user_data["photo_id"] += 1
    update.callback_query.message.edit_media(
        InputMediaPhoto(
            callback_context.user_data["photos"][
                list(callback_context.user_data["photos"].keys())[callback_context.user_data["photo_id"]]]
        )
    )
    update.effective_message.edit_caption(
        list(callback_context.user_data["photos"].keys())[callback_context.user_data["photo_id"]],
        reply_markup=make_collection_keyboard(callback_context.user_data)
    )


def handle_finish_get_collection(update: Update, _: CallbackContext):
    update.effective_message.delete()
    update.effective_message.reply_text(Strings.FINISH_GET)
    return ConversationHandler.END


class Bot:
    def __init__(self, token):
        self.updater = Updater(token)

        new_photo_handler = ConversationHandler(
            entry_points=[CommandHandler('add_photo', handle_add, run_async=True)],
            states={
                States.WAITING_PHOTO: [
                    MessageHandler(Filters.photo, handle_new_photo, run_async=True)],
                States.WAITING_NAME: [
                    MessageHandler(Filters.text & ~Filters.command, handle_name, run_async=True),
                    CommandHandler('cancel_photo', handle_cancel_photo, run_async=True)]
            },
            fallbacks=[CommandHandler('cancel', handle_cancel, run_async=True)],
            run_async=True
        )

        quiz_handler = ConversationHandler(
            entry_points=[CommandHandler('quiz', handle_start_quiz, run_async=True)],
            states={
                States.WAITING_ANSWER: [
                    CallbackQueryHandler(handle_next_question, pattern="^NEXT$"),
                    CallbackQueryHandler(handle_prev_question, pattern="^PREV$"),
                    CallbackQueryHandler(handle_finish_quiz, pattern="^FINISH$"),
                    CallbackQueryHandler(handle_person_choice, pattern=".*_PICK$")
                ]
            },
            fallbacks=[CommandHandler('cancel', handle_cancel, run_async=True),
                       CallbackQueryHandler(handle_finish_quiz, pattern="^CANCEL$")]
        )

        get_collection_handler = ConversationHandler(
            entry_points=[CommandHandler('get_collection', handle_start_get_collection, run_async=True)],
            states={
                States.WAITING_TRANSITION: [
                    CallbackQueryHandler(handle_next_photo, pattern="^NEXT$"),
                    CallbackQueryHandler(handle_prev_photo, pattern="^PREV$"),
                ]
            },
            fallbacks=[CommandHandler('cancel', handle_cancel, run_async=True),
                       CallbackQueryHandler(handle_finish_get_collection, pattern="^CANCEL$")]
        )

        self.updater.dispatcher.add_handler(CommandHandler('start', handle_start, run_async=True))
        self.updater.dispatcher.add_handler(CommandHandler('help', handle_help, run_async=True))
        self.updater.dispatcher.add_handler(get_collection_handler)
        self.updater.dispatcher.add_handler(quiz_handler)
        # self.updater.dispatcher.add_handler(new_photo_handler)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.photo, handle_new_photo, run_async=True))

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
