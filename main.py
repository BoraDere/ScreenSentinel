import sys
from vision import *
from utils import *

THRESHOLD = 0.6
AUTHORIZED_USERS_DIR = 'authorized_users'
AUTHORIZED_ENCODINGS_DIR = 'authorized_user_encodings'

running = True
authorized_encodings = {}

# TODO: use count, don't delete initial photos, read from json... 
# TODO: if none, then halt
# TODO: avoid process kill
# TODO: count sayısına göre encodeları baştan yap, dosya varsa oku yoksa oluştur. count sayısı sadece bir kişi için yeterli

# TODO: ilk runsa, hiç unauth yoksa resim çek ve sete at HER GÜN this is the logic behind re-feeding

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
    check_authorized_users(user_image_count)
    authorized_encodings = load_or_generate_encodings()

    try:
        capture_loop(camera, show_frame, wait_time, capture_duration, block_multi_user, authorized_encodings)
    except KeyboardInterrupt:
        logger("Program terminated.", 'INFO')
        running = False
        print("Program terminated.")
        sys.exit()


if __name__ == '__main__':
    main()