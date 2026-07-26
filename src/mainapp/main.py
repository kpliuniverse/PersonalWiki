from src.app import App
import logging
def main():
    logging.basicConfig(level=logging.DEBUG)
    App().run()

if __name__ == "__main__":
    main()
