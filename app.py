from dotenv import load_dotenv

from ui.chat_ui import ChatUI


load_dotenv()


def main():
    ChatUI().run()


if __name__ == '__main__':
    main()
