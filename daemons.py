import subprocess
import socket
import re
import time

internet_connected = False
ntpq_pattern = re.compile(
    r"([\*\#\+\-\~ ])"      # 0 - Peer Status
    r"([\w+\-\.(): ]+)\s+"  # 1 - Server ID
    r"([\w\.]+)\s+"         # 2 - Reference ID
    r"(\d+)\s+"             # 3 - Stratum
    r"(\w+)\s+"             # 4 - Type
    r"(\d+)\s+"             # 5 - When
    r"(\d+)\s+"             # 6 - Poll
    r"(\d+)\s+"             # 7 - Reach
    r"([\d\.]+)\s+"         # 8 - Delay
    r"([-\d\.]+)\s+"        # 9 - Offset
    r"([\d\.]+)"            # 10- Jitter
)

def socket_attempt(address: str, port: int) -> bool:
    is_successful = False
    for _ in range(0, 3):
        try:
            socket.create_connection((address, port), 2)
            is_successful = is_successful or True
        except:
            pass

    return is_successful

def ntp_daemon():
    global ntpdly
    global ntpoff
    global ntpstr
    global ntpid
    global ntpout
    global is_connected

    while(True):
        try:
            is_connected = socket_attempt("8.8.8.8", 53)
            ntpq = subprocess.run(['ntpq', '-pw'], stdout=subprocess.PIPE)
            ntpq_sh = subprocess.run(['ntpq', '-p'], stdout=subprocess.PIPE)
            ntpq = ntpq.stdout.decode('utf-8')
            ntpout = ntpq_sh.stdout.decode('utf-8')
            current_server = [
                n for n in ntpq_pattern.findall(ntpq) if n[0] == '*']

            if(current_server):
                current_server = current_server[0]
                ntpid = current_server[1]
                ntpstr = current_server[3]
                ntpdly = current_server[8]
                ntpoff = current_server[9]

        except Exception as e:
            is_connected = False
            ntpid = e

        time.sleep(3)


def ping_daemon():
    global internet_connected
    while not internet_connected:
        internet_connected = socket_attempt("8.8.8.8", 53)
        time.sleep(3)