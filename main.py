import bot
import os


def main():
    token = os.environ.get("TOKEN")
    anki_bot = bot.Bot(token)
    anki_bot.run()


if __name__ == "__main__":
    main()
