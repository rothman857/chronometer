import re
import subprocess
import time
import socket
import threading
from enum import Enum
from dataclasses import dataclass
import q


class NtpType(Enum):
    UCAST = 'u'
    BCAST = 'B'
    MCAST = 'M'
    LOCAL = 'l'
    POOL = 'p'
    SYMPEER = 's'
    MANY = 'A'


class NtpTally(Enum):
    NO_STATE = ' '
    DISCARD1 = 'x'
    DISCARD2 = '-'
    BACKUP = '#'
    PREFERRED = '+'
    PEER = '*'
    PPSPEER = 'o'


@dataclass
class NtpPeer:
    tally: NtpTally = NtpTally.NO_STATE
    server_id: str = ''
    ref_id: str = ''
    stratum: int = 16
    type: NtpType = NtpType.LOCAL
    when: int = 0
    poll: int = 0
    reach: int = 0
    delay: float = 0
    offset: float = 0
    jitter: float = 0



ntpq_pattern = re.compile(
    r"([\*\#\+\-\~ ])" +        # 0 - Peer Status
    r"([\w+\-\.(): ]+)\s+" +    # 1 - Server ID
    r"([\w\.]+)\s+" +           # 2 - Reference ID
    r"(\d+)\s+" +               # 3 - Stratum
    r"(\w+)\s+" +               # 4 - Type
    r"(\d+)\s+" +               # 5 - When
    r"(\d+)\s+" +               # 6 - Poll
    r"(\d+)\s+" +               # 7 - Reach
    r"([\d\.]+)\s+" +           # 8 - Delay
    r"([-\d\.]+)\s+" +          # 9 - Offset
    r"([\d\.]+)"                # 10- Jitter
)


ntp_peer = NtpPeer()


def ntp_daemon():
    global ntp_peer

    while(True):
        try:
            ntpq_full = subprocess.run(['ntpq', '-pw'], stdout=subprocess.PIPE)
            ntpq_sh = subprocess.run(['ntpq', '-p'], stdout=subprocess.PIPE)
            ntpq_full = ntpq_full.stdout.decode('utf-8')
            ntpout = ntpq_sh.stdout.decode('utf-8')
            ntp_peer_data = q / ntpq_pattern.findall(ntpq_full)
            ntp_servers = [
                NtpPeer(
                    tally=NtpTally(p[0]),
                    server_id=p[1],
                    ref_id=p[2],
                    stratum=p[3],
                    type=NtpType(p[4]),
                    when=p[5],
                    poll=p[6],
                    reach=p[7],
                    delay=p[8],
                    offset=p[9],
                    jitter=p[10]
                ) for p in ntp_peer_data
            ]

            current_peers = [s for s in ntp_servers if s.tally == NtpTally.PEER]

            if(current_peers):
                ntp_peer = current_peers[0]
            else:
                npt_peer = NtpPeer()

        except Exception as e:
            ntp_peer.ref_id = e

        time.sleep(3)




ntp_thread = threading.Thread(target=ntp_daemon)
ntp_thread.setDaemon(True)
ntp_thread.start()

