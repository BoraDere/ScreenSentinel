import sys
from vision import *
from utils import *

running = True
authorized_encodings = {}

# TODO: if none, then halt

"""
test cases:
halt while:
    DONE capturing tick
    DONE initializing auth encodings tick
    after the capturing tickkk
    DONE nth capturing
    DONE unauth detecting
"""


def main():
    global authorized_encodings, running
    settings = settings_reader('settings.json')
    camera = settings['camera']
    show_frame = str_to_bool(settings['show_frame'])
    wait_time = settings['wait_time']
    capture_duration = settings['capture_duration']
    block_multi_user = str_to_bool(settings['block_multi_user'])
    user_image_count = settings['user_image_count']
    count_limit = settings['count_limit']
    check_authorized_users(user_image_count)
    _ = check_count_limit(count_limit)
    authorized_encodings = load_or_generate_encodings()

    try:
        capture_loop(camera, show_frame, wait_time, capture_duration, block_multi_user, authorized_encodings, count_limit)
    except KeyboardInterrupt:
        logger("Program terminated.", 'INFO')
        running = False
        print("Program terminated.")
        sys.exit()


if __name__ == '__main__':
    main()