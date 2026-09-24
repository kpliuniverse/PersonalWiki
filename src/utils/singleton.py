class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonTest(metaclass=Singleton):

    def __init__(self):
        self.__words = []

    def add_word(self, word: str):
        self.__words.append(word)

    def print_words(self):
        print(" ".join(self.__words))