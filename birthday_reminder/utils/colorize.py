from termcolor import colored


class Colorize:
    @classmethod
    def info(cls, string: str) -> str:
        return colored(string, "light_cyan")

    @classmethod
    def success(cls, string: str) -> str:
        return colored(string, "light_green")

    @classmethod
    def warning(cls, string: str) -> str:
        return colored(string, "light_yellow")

    @classmethod
    def fail(cls, string: str) -> str:
        return colored(string, "light_red")
