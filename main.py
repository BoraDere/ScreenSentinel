import sys
from vision import load_or_generate_encodings, capture_loop
from utils import settings_reader, str_to_bool, logger, check_authorized_users, check_count_limit

running = True
authorized_encodings = {}


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
    # to terminate the program manually
    except KeyboardInterrupt:
        logger("Program terminated.", 'INFO')
        running = False
        sys.exit()


if __name__ == '__main__':
    main()