import json
import cv2
import threading
import face_recognition
import tkinter as tk
from tkinter import messagebox
import time
import sys
from concurrent.futures import ProcessPoolExecutor
import os
import pickle

THRESHOLD = 0.6
AUTHORIZED_USERS_DIR = 'authorized_users'
AUTHORIZED_ENCODINGS_DIR = 'authorized_user_encodings'

running = True
process_current_frame = True
# authorized_images = {
#     'Bora Dere': ['authorized_users/Bora_Dere_Front.jpg', 
#                   'authorized_users/Bora_Dere_Full_Left.jpg', 
#                   'authorized_users/Bora_Dere_Full_Right.jpg', 
#                   'authorized_users/Bora_Dere_Half_Left.jpg', 
#                   'authorized_users/Bora_Dere_Half_Right.jpg'],
# }
authorized_encodings = {}

# TODO: to exe? is it the way to not running on lockscreen and terminating in a different way than it is now?
# TODO: make settings_reader parse the arguments in he required format, exception handling for settings file name
# TODO: divide into different modules? main, capture, utils...
# TODO: count sayısına göre encodeları baştan yap, dosya varsa oku yoksa oluştur. count sayısı sadece bir kişi için yeterli
# TODO: use count, don't delete initial photos, read from json... 
# TODO: general log system
# TODO: if none, then halt
# TODO: disposal system
# TODO: avoid process kill
# TODO: authorized_users klasörü yoksa tanımlama ekranı, isim girme, isimden dir oluştur, fotoğraf çektirme, foto ekle, eğit... UI, tanımlama sayısı da  settings

"""
test cases:
halt while:
    DONE capturing
    DONE initializing auth encodings
    after the capturing, "30 secs of wait time waits for the whole 30 sec"
    DONE nth capturing
    DONE unauth detecting
"""


def str_to_bool(value: str) -> bool:
    """
    A simple function that converts an str value to bool and returns it.

    Args:
        value(str): The value that will be converted.
    
    Returns:
        (bool): Converted value.
    """
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    else:
        message = f'Formata uymayan ayar: "{value}". Ayarları kontrol edin.'
        show_error_message(message)
        sys.exit()


def show_error_message(message: str) -> None:
    """
    Function to show that an error occured.

    Args:
        message(str): Error message.
    """
    root = tk.Tk()
    root.withdraw() 
    messagebox.showerror("HATA", message)
    root.destroy()


def encode_face(face_image) -> None:
    """
    Function to encode faces using face_recognition.

    Args:
        face_image(cv2 frame): Cropped face image.

    Returns:
        encodings: Face encodings if face_encodings didn't return None, else None.
    """
    # using hog model to increase the performance a bit
    encodings = face_recognition.face_encodings(face_image, model='hog')
    if encodings:
        return encodings[0]
    else:
        return None


# def get_encodings(image_paths: list[str]) -> list:
#     """
#     Function that encodes the images within given paths. Used for initialization purposes.

#     Args:
#         image_paths(list[str]): Paths of images.

#     Returns:
#         encodings: List of encodings. Neglects None results.
#     """
#     encodings = []

#     for path in image_paths:
#         image = face_recognition.load_image_file(path)
#         encoding = face_recognition.face_encodings(image)

#         if encoding:
#             encodings.append(encoding[0])
        
#     return encodings


# def update_authorized_encodings() -> None:
#     """
#     An initializer function for authorized users.
#     """
#     print('update')
#     for user, images in authorized_images.items():
#         authorized_encodings[user] = get_encodings(images)
#     print('done')


def load_or_generate_encodings():
    print("function starts")
    authorized_encodings = {}
    if os.path.exists(AUTHORIZED_ENCODINGS_DIR):
        print("in if loop")
        # Load existing encodings
        for user_dir in os.listdir(AUTHORIZED_ENCODINGS_DIR):
            print(f'user_dir: {user_dir}')
            user_encodings = []
            user_path = os.path.join(AUTHORIZED_ENCODINGS_DIR, user_dir)
            print(f'user_path: {user_path}')
            for encoding_file in os.listdir(user_path):
                with open(os.path.join(user_path, encoding_file), 'rb') as f:
                    encoding = pickle.load(f)
                    print(f'encoding: {encoding}')
                    user_encodings.append(encoding)
            authorized_encodings[user_dir] = user_encodings
        print('if bitişi')
    else:
        # Generate encodings
        print('in else loop')
        os.makedirs(AUTHORIZED_ENCODINGS_DIR, exist_ok=True)
        for user_dir in os.listdir(AUTHORIZED_USERS_DIR):
            print(f'user_dir: {user_dir}')
            user_path = os.path.join(AUTHORIZED_USERS_DIR, user_dir)
            print(f'user_path: {user_path}')
            user_encodings_dir = os.path.join(AUTHORIZED_ENCODINGS_DIR, user_dir)
            print(f'user_encodings_dir: {user_encodings_dir}')
            os.makedirs(user_encodings_dir, exist_ok=True)
            user_encodings = []
            for image_file in os.listdir(user_path):
                image_path = os.path.join(user_path, image_file)
                print(f'image_path: {image_path}')
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    encoding = encodings[0]
                    print(f'encoding: {encoding}')
                    user_encodings.append(encoding)
                    # Save encoding
                    encoding_file_path = os.path.join(user_encodings_dir, image_file + "_Encoding")
                    with open(encoding_file_path, 'wb') as f:
                        pickle.dump(encoding, f)
                else:
                    print(f"No face encodings found in {image_file}. Skipping.")
            authorized_encodings[user_dir] = user_encodings
        print('else bitişi')
    return authorized_encodings


def settings_reader(filename: str):
    """
    A simple reader function.

    Args:
        filename(str): Name of the file that will be read.
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        print('bulunamadı. dosyanın adı settings olmalı ve JSON formatında olmalıdır')
        sys.exit()


def capture(camera: str, show_frame: str, capture_duration: int, block_multi_user: bool) -> None:
    """
    Main function that is responsible of capturing, detecting and recognizing.

    Args:
        camera(str): ID of camera given in the settings file.
        show_frame(bool): Bool value of show_frame given in the settings file.
        capture_duration(int): Duration of capture.
    """
    global running, authorized_encodings, process_current_frame

    cap = cv2.VideoCapture(camera)
    authorized_detected = False
    
    # error while opening the camera
    if not cap.isOpened():
        message = f"{camera} numaralı kamera açılamadı. Bu kameranın sistemde var olduğuna emin olun."
        show_error_message(message)
        sys.exit(message)

    start_time = time.time()

    while time.time() - start_time < capture_duration and running and not authorized_detected:
        ret, frame = cap.read()
        if not ret:
            # if not ret cap.read() doesn't return a frame, meaning there is a problem. which is mostly the camera being already used
            message = f"{camera} numaralı kamera şu anda kullanımda veya başka bir hata oluştu."
            show_error_message(message)
            sys.exit(message)

        if process_current_frame:
            # performance-wise operation
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]  # BGR to RGB conversion
            face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')
            # debugging
            # print("Face locations:", face_locations)
            # face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations, model='hog') # takes all the time
            faces = []
            for top, right, bottom, left in face_locations:
                # Debugging: Print slicing indices
                # print("Cropping with:", top, right, bottom, left)
                if 0 <= top < bottom <= rgb_small_frame.shape[0] and 0 <= left < right <= rgb_small_frame.shape[1]:
                    face = rgb_small_frame[top:bottom, left:right]
                    faces.append(face)
                # else:
                #     print("Invalid face location skipped:", top, right, bottom, left)

            # recognition part

            if faces:
                with ProcessPoolExecutor() as executor:
                    face_encodings = list(executor.map(encode_face, faces))
                del faces
            else:
                # so that compare_faces won't receive None
                # kinda unnecessary thanks to valid_face_encodings, check if this is the case
                face_encodings = []

            unauthorized_detected = False
            valid_face_encodings = [enc for enc in face_encodings if enc is not None]

            for encoding in valid_face_encodings:
                matches = face_recognition.compare_faces(
                    [enc for sublist in authorized_encodings.values() for enc in sublist], 
                    encoding, 
                    tolerance=THRESHOLD,
                )

                if block_multi_user:
                    print('yes block_multi_user')
                    # order of these two ifs can be used in block_multi_user??
                    if not any(matches):
                        unauthorized_detected = True
                        break

                    if any(matches):  # This condition is met if an authorized person is detected
                        print("Authorized person detected. Stopping capture.")
                        authorized_detected = True
                        break  # Exit the loop to stop capturing
                else:
                    print('no block_multi_user')
                    if any(matches):  # This condition is met if an authorized person is detected
                        print("Authorized person detected. Stopping capture.")
                        authorized_detected = True
                        break  # Exit the loop to stop capturing

                    if not any(matches):
                        unauthorized_detected = True
                        break

            if unauthorized_detected:
                # change it from being an immediate action with window panes
                # it shouldn't be running False, just screen lock
                print("unauth detected")
                running = False
                # UnboundLocalError: local variable 'running' referenced before assignment
                # fixed but check again
                break

            if show_frame:
                for top, right, bottom, left in face_locations:
                    top *= 4; right *= 4; bottom *= 4; left *= 4 
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.imshow('Webcam', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): # for debugging purposes
                break

        process_current_frame = not process_current_frame # unbound bunun yüzünden

    cap.release()
    if show_frame:
        cv2.destroyAllWindows()


def capture_callback():
    """
    Callback function for threading timer.
    """
    global running
    if not running:  
        return

    settings = settings_reader('settings.json')
    camera = settings['camera']
    show_frame = str_to_bool(settings['show_frame'])
    wait_time = settings['wait_time']
    capture_duration = settings['capture_duration']
    block_multi_user = str_to_bool(settings['block_multi_user'])
    capture(camera, show_frame, capture_duration, block_multi_user)
    if running:  
        # sleep_time = 30  
        # elapsed = 0
        # while running and elapsed < sleep_time:  
        #     time.sleep(1)  
        #     elapsed += 1
        # if running:  
        #     threading.Timer(30, capture_callback).start()
        threading.Timer(wait_time, capture_callback).start()


if __name__ == '__main__':
    authorized_encodings = load_or_generate_encodings()
    for user, enc in authorized_encodings.items():
        print(f'{user}: {enc}')
    capture_callback()
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        print("Program terminated.")
        sys.exit()