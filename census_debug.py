from glob import glob
import time

debug = True
start_time = None


def start_timer():
    global start_time
    start_time = time.time()


def print_timer(msg):
    global start_time
    duration = time.time() - start_time
    start_time = time.time()
    if debug:
        print(f'{msg}: {duration} seconds')
