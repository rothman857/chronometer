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


if __name__ == '__main__':
    pass
