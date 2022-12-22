import os


def reset_cursor() -> None:
    print("\33[0;0H", end="")


def show_cursor(on: bool = True) -> None:
    if on:
        print("\33[?25h")
    else:
        print("\33[?25l")


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


class Color:
    class BG:
        BLACK = "\33[40m"
        BRIGHT_BLUE = "\33[104m"
        RED = "\33[41m"

    class FG:
        WHITE = "\33[97m"
        BRIGHT_BLUE = "\33[94m"
        DARK_GRAY = "\33[90m"
    
    reset = "\33[0m"


if __name__ == '__main__':
    pass
