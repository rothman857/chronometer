import os


def reset_cursor() -> None:
    print("\033[0;0H", end="")


def show_cursor(on: bool = True) -> None:
    if on:
        print("\x1b[?25h")
    else:
        print("\x1b[?25l")


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

class Color:
    class BG:
        BLACK = "\x1b[40m"
        BRIGHT_BLUE = "\x1b[104m"
        RED = "\x1b[41m"

    class FG:
        WHITE = "\x1b[97m"
        BRIGHT_BLUE = "\x1b[94m"
        DARK_GRAY = "\x1b[90m"


if __name__ == '__main__':
    pass
