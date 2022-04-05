import os


def reset_cursor():
    print("\033[0;0H", end="")


def show_cursor(on: bool = True):
    if on:
        print("\x1b[?25h")
    else:
        print("\x1b[?25l")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
