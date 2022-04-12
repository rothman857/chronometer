import math

def acos(x: float) -> float:
    return math.degrees(math.acos(x))


def asin(x: float) -> float:
    return math.degrees(math.asin(x))


def atan(x: float) -> float:
    return math.degrees(math.atan(x))


def sin(deg: float) -> float:
    return math.sin(math.radians(deg))


def cos(deg: float) -> float:
    return math.cos(math.radians(deg))


def tan(deg: float) -> float:
    return math.tan(math.radians(deg))


if __name__ == '__main__':
    pass