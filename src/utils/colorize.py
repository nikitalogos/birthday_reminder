class Colorize:
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    @classmethod
    def info(cls, string):
        return f'{cls.OKCYAN}{string}{cls.ENDC}'

    @classmethod
    def success(cls, string):
        return f'{cls.OKGREEN}{string}{cls.ENDC}'

    @classmethod
    def fail(cls, string):
        return f'{cls.FAIL}{string}{cls.ENDC}'