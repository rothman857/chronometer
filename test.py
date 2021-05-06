import os
import re


# Terminal coloring
BLACK_BG = "\x1b[40m"
WHITE_FG = "\x1b[97m"
L_BLUE_FG = "\x1b[94m"
L_BLUE_BG = "\x1b[104m"
D_GRAY_FG = "\x1b[90m"
RST_COLORS = "\x1b[0m"

themes = [
    BLACK_BG,  # background
    WHITE_FG,  # text
    L_BLUE_FG, # table borders
    L_BLUE_BG, # text highlight
    D_GRAY_FG  # progress bar dim
] 



class Screen:
    def __init__(self):
        self.rows = os.get_terminal_size().lines
        self.columns = os.get_terminal_size().columns
        self.content = ''
        self.length = 0

    



test = themes[2] + chr(0x255A) + chr(0x255A) + themes[1]
# test = str(test.encode('unicode_escape'))
print(test)
print(len(test))


result = re.findall('\[\d+m', test)
print(result)
l = 0
for regex in ['\[\d+m','\\x1b']:
    for i in re.findall(regex, test):
        print(i)
        l += (len(i))
print(l)
print(len(test) - l)

def printable_length()

# strip_ANSI_pat = re.compile(r"""
#     \x1b     # literal ESC
#     \[       # literal [
#     [;\d]*   # zero or more digits or semicolons
#     [A-Za-z] # a letter
#     """, re.VERBOSE).sub


# \\x1b,[94m,\\u255a,\\x1b,[97m