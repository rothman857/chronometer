import re
import subprocess
import time
import threading
from enum import Enum
from dataclasses import dataclass


class State(Enum):
    NO_STATE = ' '
    DISCARD1 = 'x'
    DISCARD2 = '-'
    BACKUP = '#'
    PREFERRED = '+'
    PEER = '*'
    PPSPEER = 'o'


class RegexPattern:
    pattern = re.compile(
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

    refid = re.compile(r"^\.(\S+)\.$")


@dataclass
class NtpPeer:
    state: State = State.NO_STATE
    server_id: str = 'NO SYNC'
    ref_id: str = ''
    stratum: int = 16
    type: str = ''
    when: int = 0
    poll: int = 0
    reach: int = 0
    delay: float = 0
    offset: float = 0
    jitter: float = 0
    source: str = ''

    def __post_init__(self):
        source = RegexPattern.refid.findall(self.ref_id)
        self.source = source[0] if source else ''


peer = NtpPeer()


def ntp_daemon() -> None:
    global peer

    while(True):
        try:
            ntpq_full = subprocess.run(
                ['ntpq', '-pw'], stdout=subprocess.PIPE
            ).stdout.decode('utf-8')
            ntp_peer_data = RegexPattern.pattern.findall(ntpq_full)
            ntp_servers = [
                NtpPeer(
                    state=State(p[0]),
                    server_id=p[1],
                    ref_id=p[2],
                    stratum=p[3],
                    type=p[4],
                    when=p[5],
                    poll=p[6],
                    reach=p[7],
                    delay=p[8],
                    offset=p[9],
                    jitter=p[10]
                ) for p in ntp_peer_data
            ]

            current_peers = [s for s in ntp_servers if s.state == State.PEER]
            if(current_peers):
                peer = current_peers[0]
            else:
                peer = NtpPeer()
        except Exception as e:
            peer.server_id = str(e)
        time.sleep(3)


def main() -> None:
    thread = threading.Thread(target=ntp_daemon)
    thread.setDaemon(True)
    thread.start()


if __name__ == '__main__':
    pass
else:
    main()
