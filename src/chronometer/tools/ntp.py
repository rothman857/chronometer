import re
import subprocess
import time
import threading
from enum import Enum
from dataclasses import dataclass
import os


class State(Enum):
    NO_STATE = ' '
    DISCARD1 = 'x'
    DISCARD2 = '-'
    BACKUP = '#'
    PREFERRED = '+'
    PEER = '*'
    PPSPEER = 'o'


class ServiceStatus(Enum):
    ACTIVE = 0
    INACTIVE = 768
    NOTFOUND = 1024


service_status = ServiceStatus.NOTFOUND


class RegexPattern:
    pattern = re.compile(
        r"([\*\#\+\-\~ ])"       # 0 - Peer Status
        r"([\w+\-\.(): ]+)\s+"   # 1 - Server ID
        r"([\w\.]+)\s+"          # 2 - Reference ID
        r"(\d+)\s+"              # 3 - Stratum
        r"(\w+)\s+"              # 4 - Type
        r"(\d+)\s+"              # 5 - When
        r"(\d+)\s+"              # 6 - Poll
        r"(\d+)\s+"              # 7 - Reach
        r"([\d\.]+)\s+"          # 8 - Delay
        r"\+*([\-\d\.]+)\s+"         # 9 - Offset
        r"([\d\.]+)"             # 10- Jitter
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
        ref_ids = {
            "GOES",  # Geosynchronous Orbit Environment Satellite
            "GPS",   # Global Position System
            "GAL",   # Galileo Positioning System
            "PPS",   # Generic pulse-per-second
            "IRIG",  # Inter-Range Instrumentation Group
            "WWVB",  # LF Radio WWVB Ft. Collins, CO 60 kHz
            "DCF",   # LF Radio DCF77 Mainflingen, DE 77.5 kHz
            "HBG",   # LF Radio HBG Prangins, HB 75 kHz
            "MSF",   # LF Radio MSF Anthorn, UK 60 kHz
            "JJY",   # LF Radio JJY Fukushima, JP 40 kHz, Saga, JP 60 kHz
            "LORC",  # MF Radio LORAN C station, 100 kHz
            "TDF",   # MF Radio Allouis, FR 162 kHz
            "CHU",   # HF Radio CHU Ottawa, Ontario
            "WWV",   # HF Radio WWV Ft. Collins, CO
            "WWVH",  # HF Radio WWVH Kauai, HI
            "NIST",  # NIST telephone modem
            "ACTS",  # NIST telephone modem
            "USNO",  # USNO telephone modem
            "PTB",   # European telephone modem
        }
        source = RegexPattern.refid.findall(self.ref_id)
        if source and source[0] in ref_ids:
            self.source = source[0]


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


def run() -> None:
    global service_status
    ntp_service_response = os.system('systemctl status ntp')
    time.sleep(1)

    if ntp_service_response == 0:
        service_status = ServiceStatus.ACTIVE
    elif ntp_service_response == 768:
        service_status = ServiceStatus.INACTIVE
    else:
        service_status = ServiceStatus.NOTFOUND

    if service_status == ServiceStatus.ACTIVE:
        thread = threading.Thread(target=ntp_daemon)
        thread.setDaemon(True)
        thread.start()


if __name__ == '__main__':
    pass
else:
    run()
