from src.app import App
import logging
def main():
    import multiprocessing
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.DEBUG)
    App().run()

if __name__ == "__main__":
    main()
