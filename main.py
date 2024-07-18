import json
import cv2
import face_recognition
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import time
import sys
from concurrent.futures import ProcessPoolExecutor
import os
import pickle
from datetime import datetime
import subprocess

THRESHOLD = 0.6
AUTHORIZED_USERS_DIR = 'authorized_users'
AUTHORIZED_ENCODINGS_DIR = 'authorized_user_encodings'

running = True
process_current_frame = True
authorized_encodings = {}

# TODO: divide into different modules? main, capture, utils...
# TODO: use count, don't delete initial photos, read from json... 
# TODO: if none, then halt
# TODO: avoid process kill
# TODO: count sayısına göre encodeları baştan yap, dosya varsa oku yoksa oluştur. count sayısı sadece bir kişi için yeterli
# TODO: authorized_users klasörü yoksa tanımlama ekranı, isim girme, isimden dir oluştur, fotoğraf çektirme, foto ekle, eğit... 
#   UI, tanımlama sayısı da  settings
# TODO: kamera seçtirme devid, concurrent with the former one
# TODO: if flow starts from the point which auth_users image folder does not exist it also should do the encodings

"""
test cases:
halt while:
    DONE capturing tick
    DONE initializing auth encodings tick
    after the capturing tickkk
    DONE nth capturing
    DONE unauth detecting
"""


def ask_camera_selection(camera_names):
    def on_select():
        selected_index.set(camera_names.index(cameras_listbox.get(cameras_listbox.curselection())))
        root.destroy()

    root = tk.Tk()
    root.title("Select Camera")
    selected_index = tk.IntVar(value=0)  # default 

    cameras_listbox = tk.Listbox(root)
    cameras_listbox.pack()

    for name in camera_names:
        cameras_listbox.insert(tk.END, name)

    select_button = tk.Button(root, text="Select", command=on_select)
    select_button.pack()

    root.mainloop()
    return selected_index.get()


def list_cameras(max_checks=10):
    available_cameras = []
    for i in range(max_checks):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras


def list_cameras_with_powershell():
    command = ["powershell", "-Command", "Get-CimInstance Win32_PnPEntity | ? { $_.service -eq 'usbvideo' } | Select-Object -Property Name"]
    result = subprocess.run(command, capture_output=True, text=True)
    
    camera_names = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    camera_names.remove('Name')
    camera_names.remove('----')
    
    return camera_names


def ask_user_name():
    root = tk.Tk()
    root.withdraw()  

    user_name = simpledialog.askstring("Name", "Please enter your name:")
    
    root.destroy()
    
    return user_name


def check_authorized_users(user_image_count: int):
    """
    This function is intended to run only in the case which there is no authorized_users folder is prepared before the initial run of the code,
    which is actually opposite of the advised usage. 
    MUST CLARIFY THE ACTUAL USAGE SCENARIOS
    """
    if not os.path.exists(AUTHORIZED_USERS_DIR):
        os.makedirs(AUTHORIZED_USERS_DIR)
        user_name = ask_user_name()
        user_dir = os.path.join(AUTHORIZED_USERS_DIR, user_name)
        os.makedirs(user_dir)

        # camera selection part
        camera_names = list_cameras_with_powershell()
        selected_camera_index = ask_camera_selection(camera_names)
        # write to json file
        opencv_camera_index = list_cameras()[selected_camera_index]

        cap = cv2.VideoCapture(opencv_camera_index)

        # capture photo
        for i in range(user_image_count):
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to capture image")
                    break
                cv2.imshow('Capture Photo', frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('s'):
                    # save photo
                    photo_path = os.path.join(user_dir, f"{user_name}_init_{i+1}.jpg")
                    cv2.imwrite(photo_path, frame)
                    print(f"Photo saved: {photo_path}")
                    break  
                elif key == ord('q'):  # to quit
                    break

            if key == ord('q'):  
                break

        cap.release()
        cv2.destroyAllWindows()


def logger(log: str, type: str) -> None:
    with open('logs.txt', 'a') as w:
        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        w.write(f'[{dt}] {type}: {log}\n')


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
        message = f'Value does not fit the format: "{value}". Check the settings.'
        show_error_message(message)
        logger(message, 'ERROR')
        sys.exit()


def show_error_message(message: str) -> None:
    """
    Function to show that an error occured.

    Args:
        message(str): Error message.
    """
    root = tk.Tk()
    root.withdraw() 
    messagebox.showerror("ERROR", message)
    root.destroy()


def encode_face(face_image) -> list | None:
    """
    Function to encode faces using face_recognition.

    Args:
        face_image(cv2 frame): Cropped face image.

    Returns:
        encodings: Face encoding if face_encodings didn't return None, else None.
    """
    # using hog model to increase the performance a bit
    encodings = face_recognition.face_encodings(face_image, model='hog')
    if encodings:
        return encodings[0]
    else:
        return None


def load_or_generate_encodings():
    authorized_encodings = {}

    if os.path.exists(AUTHORIZED_ENCODINGS_DIR):
        for user_dir in os.listdir(AUTHORIZED_ENCODINGS_DIR):
            user_encodings = []
            user_path = os.path.join(AUTHORIZED_ENCODINGS_DIR, user_dir)

            for encoding_file in os.listdir(user_path):
                with open(os.path.join(user_path, encoding_file), 'rb') as f:
                    encoding = pickle.load(f)
                    user_encodings.append(encoding)

            authorized_encodings[user_dir] = user_encodings            
    else:
        os.makedirs(AUTHORIZED_ENCODINGS_DIR, exist_ok=True)
        for user_dir in os.listdir(AUTHORIZED_USERS_DIR):
            user_path = os.path.join(AUTHORIZED_USERS_DIR, user_dir)
            user_encodings_dir = os.path.join(AUTHORIZED_ENCODINGS_DIR, user_dir)
            os.makedirs(user_encodings_dir, exist_ok=True)
            user_encodings = []

            for image_file in os.listdir(user_path):
                image_path = os.path.join(user_path, image_file)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    encoding = encodings[0]
                    user_encodings.append(encoding)
                    encoding_file_path = os.path.join(user_encodings_dir, image_file + "_Encoding")

                    with open(encoding_file_path, 'wb') as f:
                        pickle.dump(encoding, f)

            authorized_encodings[user_dir] = user_encodings

    return authorized_encodings


def settings_reader(filename: str) -> (list | None):
    """
    A simple reader function.

    Args:
        filename(str): Name of the file that will be read.
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        message = 'Settings file cannot be found. It must be names as "settings" and the file format must be JSON.'
        print(message)
        logger(message, 'ERROR')
        sys.exit()


def capture(camera: str, show_frame: str, capture_duration: int, block_multi_user: bool, cap: cv2.VideoCapture) -> None:
    """
    Main function that is responsible of capturing, detecting and recognizing.

    Args:
        camera(str): ID of camera given in the settings file.
        show_frame(bool): Bool value of show_frame given in the settings file.
        capture_duration(int): Duration of capture.
    """
    global running, authorized_encodings, process_current_frame

    authorized_detected = False
    
    # error while opening the camera
    if not cap.isOpened():
        message = f"Camera {camera} cannot be used. Be sure that this device exists."
        logger(message, 'ERROR')
        show_error_message(message)
        sys.exit(message)

    start_time = time.time()

    while time.time() - start_time < capture_duration and running and not authorized_detected:
    # while running and not authorized_detected:
        ret, frame = cap.read()

        if not ret:
            # if cap.read() doesn't return a frame, meaning there is a problem. which is mostly the camera being already used
            message = f"Camera {camera} is being used or another error occured."
            logger(message, 'ERROR')
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
                if 0 <= top < bottom <= rgb_small_frame.shape[0] and 0 <= left < right <= rgb_small_frame.shape[1]:
                    face = rgb_small_frame[top:bottom, left:right]
                    faces.append(face)

            # recognition part

            if faces:
                with ProcessPoolExecutor() as executor:
                    face_encodings = list(executor.map(encode_face, faces))
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
                    # order of these two ifs can be used in block_multi_user??
                    if not any(matches):
                        unauthorized_detected = True
                        break

                    if any(matches):
                        message = "Authorized person detected. Stopping capture."  
                        print(message)
                        logger(message, 'INFO')
                        authorized_detected = True
                        break  
                else:
                    print('no block_multi_user')
                    if any(matches):  
                        message = "Authorized person detected. Stopping capture."  
                        print(message)
                        logger(message, 'INFO')
                        authorized_detected = True
                        break  

                    if not any(matches):
                        unauthorized_detected = True
                        break


            if unauthorized_detected:
                # change it from being an immediate action with window panes
                # it shouldn't be running False, just screen lock
                message = "Unauthorized person detected. System goes to sleep."
                print(message)
                logger(message, 'INFO')
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

    # cap.release()
    if show_frame:
        cv2.destroyAllWindows()


def capture_loop(camera: str, show_frame: str, wait_time, capture_duration: int, block_multi_user: bool):
    """
    Callback function for threading timer.
    """
    global running
    if not running:  
        return
    
    cap = cv2.VideoCapture(camera)    
        # sleep_time = 30  
        # elapsed = 0
        # while running and elapsed < sleep_time:  
        #     time.sleep(1)  
        #     elapsed += 1
        # if running:  
        #     threading.Timer(30, capture_callback).start()
        # threading.Timer(wait_time, capture_callback).start(),
    while True:
        capture(camera, show_frame, capture_duration, block_multi_user, cap)
        time.sleep(wait_time)


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
        capture_loop(camera, show_frame, wait_time, capture_duration, block_multi_user)
    except KeyboardInterrupt:
        logger("Program terminated.", 'INFO')
        running = False
        print("Program terminated.")
        sys.exit()


if __name__ == '__main__':
    main()