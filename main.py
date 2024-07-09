import json
import cv2
import threading
import face_recognition
import tkinter as tk
from tkinter import messagebox
import time
import sys
from concurrent.futures import ThreadPoolExecutor

THRESHOLD = 0.6

running = True
process_current_frame = True
authorized_images = {
    'Bora Dere': ['authorized_users/Bora_Dere_Front.jpg', 
                  'authorized_users/Bora_Dere_Full_Left.jpg', 
                  'authorized_users/Bora_Dere_Full_Right.jpg', 
                  'authorized_users/Bora_Dere_Half_Left.jpg', 
                  'authorized_users/Bora_Dere_Half_Right.jpg'],
}
authorized_encodings = {}

### TODO: draw_frame in settings found to be redundant, because it will appear only for 10 seconds iff show_frame is True
# TODO: to exe? is it the way to not running on lockscreen and terminating in a different way than it is now?
# TODO: make settings_reader parse the arguments in he required format?
# TODO: divide into different modules? main, capture, utils...
# TODO: do camera check(s) before encoding update - REALLY?
### TODO: when it detects an authorized user, stop capturing? 
### No need for re-feeding with newer captured frames.
### halt when an unauth looks at the screen at the same time with an auth person?
# TODO: exception handling for settings file name

"""
test cases:
halt when:
    DONE capturing
    DONE initializing auth encodings
    after the capturing, "30 secs of wait time waits for the whole 30 sec"
    DONE nth capturing
    DONE unauth detecting
"""


def str_to_bool(value: str) -> bool:
    """
    A simple function that converts an str value to bool and returns it.

    ### Args:
        value(str): The value that will be converted.
    
    ### Returns:
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

    ### Args:
        message(str): Error message.
    """
    root = tk.Tk()
    root.withdraw() 
    messagebox.showerror("HATA", message)
    root.destroy()


def encode_face(face_image) -> None:
    """
    Function to encode faces using face_recognition.

    ### Args:
        face_image(cv2 frame): Cropped face image.

    ### Returns:
        encodings: Face encodings if face_encodings didn't return None, else None.
    """
    encodings = face_recognition.face_encodings(face_image, model='hog')
    if encodings:
        return encodings[0]
    else:
        return None


def get_encodings(image_paths: list[str]) -> list:
    """
    Function that encodes the images within given paths. Used for initialization purposes.

    ### Args:
        image_paths(list[str]): Paths of images.

    ### Returns:
        encodings: List of encodings. Neglects None results.
    """
    encodings = []

    for path in image_paths:
        image = face_recognition.load_image_file(path)
        encoding = face_recognition.face_encodings(image)

        if encoding:
            encodings.append(encoding[0])
        
    return encodings


def update_authorized_encodings() -> None:
    """
    An initializer function for authorized users.
    """
    print('update')
    for user, images in authorized_images.items():
        authorized_encodings[user] = get_encodings(images)
    print('done')


def settings_reader(filename: str):
    """
    A simple reader function.

    ### Args:
        filename(str): Name of the file that will be read.
    """
    with open(filename, 'r') as f:
        return json.load(f)


def capture(camera: str, show_frame: str, draw_frame: str, capture_duration: int=10):
    """
    Main function that is responsible of capturing, detecting and recognizing.

    ### Args:
        camera(str): ID of camera given in the settings file.
        show_frame(bool): Bool value of show_frame given in the settings file.
        draw_frame(bool): Bool value of draw_frame given in the settings file.
        capture_duration(int): Pre-defined as 10, duration of capture.
    """
    global running, authorized_encodings, process_current_frame

    cap = cv2.VideoCapture(camera)
    
    if not cap.isOpened():
        message = f"{camera} numaralı kamera açılamadı. Bu kameranın sistemde var olduğuna emin olun."
        show_error_message(message)
        sys.exit(message)

    start_time = time.time()

    while time.time() - start_time < capture_duration and running:
        ret, frame = cap.read()
        if not ret:
            message = f"{camera} numaralı kamera şu anda kullanımda veya başka bir hata oluştu."
            show_error_message(message)
            sys.exit(message)

        if process_current_frame:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]  # BGR to RGB conversion
            face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')
            print("Face locations:", face_locations)
            # face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations, model='hog') # takes all the time
            faces = []
            for top, right, bottom, left in face_locations:
                # Debugging: Print slicing indices
                print("Cropping with:", top, right, bottom, left)
                if 0 <= top < bottom <= rgb_small_frame.shape[0] and 0 <= left < right <= rgb_small_frame.shape[1]:
                    face = rgb_small_frame[top:bottom, left:right]
                    faces.append(face)
                # else:
                #     print("Invalid face location skipped:", top, right, bottom, left)

            # recognition part

            if faces:
                with ThreadPoolExecutor() as executor:
                    face_encodings = list(executor.map(encode_face, faces))
            else:
                face_encodings = []

            unauthorized_detected = False
            valid_face_encodings = [enc for enc in face_encodings if enc is not None]


            for encoding in valid_face_encodings:
                matches = face_recognition.compare_faces(
                    [enc for sublist in authorized_encodings.values() for enc in sublist], 
                    encoding, 
                    tolerance=THRESHOLD,
                )

                if not any(matches):
                    unauthorized_detected = True
                    break

            if unauthorized_detected:
                # change it from being an immediate action with window panes
                print("unauth detected")
                running = False
                # UnboundLocalError: local variable 'running' referenced before assignment
                # fixed but check again
                break

            if show_frame:
                if draw_frame:
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
    draw_frame = str_to_bool(settings['draw_frame']) 
    capture(camera, show_frame, draw_frame)
    if running:  
        # sleep_time = 30  
        # elapsed = 0
        # while running and elapsed < sleep_time:  
        #     time.sleep(1)  
        #     elapsed += 1
        # if running:  
        #     threading.Timer(30, capture_callback).start()
        threading.Timer(30, capture_callback).start()


if __name__ == '__main__':
    update_authorized_encodings()
    capture_callback()
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        print("Program terminated.")
        sys.exit()