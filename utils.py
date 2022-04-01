import os

def reset_cursor():
    print("\033[0;0H", end="")


def move_cursor_down(n=1):
    print('\033[' + str(n) + 'B', end='')

def move_cursor_up(n=1):
    print('\033[' + str(n) + 'A', end='')

def show_cursor(on: bool = True):
    if on:
        os.system("setterm -cursor on")
    else:
        os.system("setterm -cursor off")

def clear_screen():
    os.system("clear")