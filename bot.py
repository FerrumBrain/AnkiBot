import os
import weighted_random
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from strings import Strings
from states import States
import pandas as pd


df = pd.read_csv('names.csv', encoding='windows-1251')

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
    elif update.effective_message.caption.split()[0] not in df.values:
        callback_context.user_data["temporary"] = update.message.photo[-1].file_id
        update.effective_message.reply_text(Strings.UNKNOWN_NAME)
        return States.WAITING_NAME

    update.effective_message.reply_text(Strings.GOT_PHOTO)
    callback_context.user_data["photos"][update.effective_message.caption] = update.message.photo[-1].file_id
    if "guesses" not in callback_context.user_data.keys():
        callback_context.user_data["guesses"] = {}
    callback_context.user_data["guesses"][update.effective_message.caption] = [0, 0]
    return States.WAITING_PHOTO


def handle_name(update: Update, callback_context: CallbackContext):
    if update.effective_message.text in callback_context.user_data["photos"].keys():
        update.effective_message.reply_text(Strings.OLD_NAME)
        return States.WAITING_NAME
    elif update.effective_message.text.split()[0] not in df.values:
        update.effective_message.reply_text(Strings.UNKNOWN_NAME)
        return States.WAITING_NAME
    if "photos" not in callback_context.user_data.keys():
        callback_context.user_data["photos"] = {}
    callback_context.user_data["photos"][update.effective_message.text] = callback_context.user_data["temporary"]
    update.effective_message.reply_text(Strings.GOT_NAME)
    if "guesses" not in callback_context.user_data.keys():
        callback_context.user_data["guesses"] = {}
    callback_context.user_data["guesses"][update.effective_message.text] = [0, 0]
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

    next_button = InlineKeyboardButton(Strings.NEXT, callback_data="NEXT")
    finish_button = InlineKeyboardButton(Strings.FINISH, callback_data="FINISH")

    if data["question_id"] == data["total_questions"] - 1:
        buttons.append([finish_button])
    elif data["question_id"] != 0:
        buttons.append([next_button])
        buttons.append([InlineKeyboardButton(Strings.CANCEL_QUIZ, callback_data="CANCEL")])
    else:
        buttons.append([next_button])
        buttons.append([InlineKeyboardButton(Strings.CANCEL_QUIZ, callback_data="CANCEL")])

    return InlineKeyboardMarkup(buttons)


def handle_start_quiz(update: Update, callback_context: CallbackContext):
    if "photos" in callback_context.user_data.keys():
        right_name = weighted_random.choice(callback_context.user_data["guesses"], list(callback_context.user_data["photos"].keys()))

        callback_context.user_data["questions"] = []
        callback_context.user_data["question_id"] = 0
        callback_context.user_data["questions_asked"] = 0
        callback_context.user_data["list_not_asked_questions"] = list(callback_context.user_data["photos"].keys())
        callback_context.user_data["total_questions"] = min(20, len(callback_context.user_data["photos"]))
        callback_context.user_data["user_answers"] = []

        update.effective_message.reply_photo(
            callback_context.user_data["photos"][right_name],
            reply_markup=make_quiz_keyboard(right_name, callback_context.user_data, True)
        )
        return States.WAITING_ANSWER

    update.effective_message.reply_text(Strings.EMPTY_LIST)


def handle_start_test_quiz(update: Update, callback_context: CallbackContext):
    callback_context.user_data["is_test"] = True

    callback_context.user_data["old_data"] = {}
    if "photos" in callback_context.user_data.keys():
        callback_context.user_data["old_data"]["photos"] = callback_context.user_data["photos"]
    else:
        callback_context.user_data["old_data"]["photos"] = {}
    if "guesses" in callback_context.user_data.keys():
        callback_context.user_data["old_data"]["guesses"] = callback_context.user_data["guesses"]
    else:
        callback_context.user_data["old_data"]["guesses"] = {}

    callback_context.user_data["photos"] = {}
    callback_context.user_data["guesses"] = {}
    test_photos = {
        "Мэрилин Монро": os.environ.get("MONRO"),
        "Микки Маус": os.environ.get("MICKEY"),
        "Гомер Симпсон":  os.environ.get("HOMER"),
        "Альберт Эйнштейн":  os.environ.get("EINSTEIN")
    }
    for name in test_photos.keys():
        callback_context.user_data["photos"][name] = test_photos[name]
        callback_context.user_data["guesses"][name] = [0, 0]

    handle_start_quiz(update, callback_context)
    return States.WAITING_ANSWER


def handle_next_question(update: Update, callback_context: CallbackContext):
    if callback_context.user_data["user_answers"][callback_context.user_data["question_id"]] is None:
        update.callback_query.answer(Strings.SELECT, show_alert=True)
        return

    if callback_context.user_data["user_answers"][callback_context.user_data["question_id"]] == callback_context.user_data["questions"][callback_context.user_data["question_id"]][0]:
        update.callback_query.answer(Strings.CORRECT_ANSWER, show_alert=True)
    else:
        update.callback_query.answer(f'{Strings.INCORRECT_ANSWER}\n{Strings.YOUR_ANSWER}{callback_context.user_data["user_answers"][callback_context.user_data["question_id"]]}\n{Strings.RIGHT_ANSWER}{callback_context.user_data["questions"][callback_context.user_data["question_id"]][0]}', show_alert=True)

    update.callback_query.answer()
    if callback_context.user_data["question_id"] == callback_context.user_data["questions_asked"] - 1:
        right_name = weighted_random.choice(callback_context.user_data["guesses"], callback_context.user_data["list_not_asked_questions"])
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
    if callback_context.user_data["user_answers"][callback_context.user_data["question_id"]] is None and not callback_context.user_data["is_cancel"]:
        update.callback_query.answer(Strings.SELECT, show_alert=True)
        return

    if not callback_context.user_data["is_cancel"]:
        if callback_context.user_data["user_answers"][callback_context.user_data["question_id"]] == callback_context.user_data["questions"][callback_context.user_data["question_id"]][0]:
            update.callback_query.answer(Strings.CORRECT_ANSWER, show_alert=True)
        else:
            update.callback_query.answer(f'{Strings.INCORRECT_ANSWER}\n{Strings.YOUR_ANSWER}{callback_context.user_data["user_answers"][callback_context.user_data["question_id"]]}\n{Strings.RIGHT_ANSWER}{callback_context.user_data["questions"][callback_context.user_data["question_id"]][0]}', show_alert=True)


    update.effective_message.delete()
    right_answer = 0
    for index, result in enumerate(zip(callback_context.user_data["user_answers"],
                                       callback_context.user_data["questions"])):
        current_answer, current_right_answer = result
        current_right_answer = current_right_answer[0]
        if current_answer == current_right_answer:
            right_answer += 1
            callback_context.user_data["guesses"][current_right_answer][0] += 1
        callback_context.user_data["guesses"][current_right_answer][1] += 1

    result = right_answer / callback_context.user_data['questions_asked']
    if result <= 0.4 or right_answer == 0:
        quality = Strings.BAD_RESULT
    elif result <= 0.8:
        quality = Strings.GOOD_RESULT
    else:
        quality = Strings.SUPER_RESULT

    format_result = format(result * 100, ".2f")
    update.effective_message.reply_text(f"{Strings.RESULT}{format_result}%\n\n{quality}")

    if callback_context.user_data["is_test"]:
        callback_context.user_data["guesses"] = callback_context.user_data["old_data"]["guesses"]
        callback_context.user_data["photos"] = callback_context.user_data["old_data"]["photos"]

    callback_context.user_data["is_cancel"] = False
    callback_context.user_data["is_test"] = False

    return ConversationHandler.END


def handle_cancel_quiz(update: Update, callback_context: CallbackContext):
    callback_context.user_data["is_cancel"] = True
    return handle_finish_quiz(update, callback_context)


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
            entry_points=[CommandHandler('quiz', handle_start_quiz, run_async=True),
                          CommandHandler('test_quiz', handle_start_test_quiz, run_async=True)],
            states={
                States.WAITING_ANSWER: [
                    CallbackQueryHandler(handle_next_question, pattern="^NEXT$"),
                    CallbackQueryHandler(handle_finish_quiz, pattern="^FINISH$"),
                    CallbackQueryHandler(handle_person_choice, pattern=".*_PICK$")
                ]
            },
            fallbacks=[CommandHandler('cancel', handle_cancel, run_async=True),
                       CallbackQueryHandler(handle_cancel_quiz, pattern="^CANCEL$")]
        )

        get_collection_handler = ConversationHandler(
            entry_points=[CommandHandler('collection', handle_start_get_collection, run_async=True)],
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
        self.updater.dispatcher.add_handler(new_photo_handler)
        # self.updater.dispatcher.add_handler(MessageHandler(Filters.photo, handle_new_photo, run_async=True))

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
