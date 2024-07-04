import json
import cv2
import threading
import face_recognition
import tkinter as tk
from tkinter import messagebox
import time

running = True

# TODO: Exception handling on str_to_bool function, maybe display error message?
# TODO: draw_frame in settings found to be redundant, because it will appear only for 10 seconds iff show_frame is True
# TODO: to exe? is it the way to not running on lockscreen and terminating in a different way than it is now?
# TODO: make settings_reader parse the arguments in he required format?
# TODO: divide into different modules? main, capture, utils...


def str_to_bool(value: str) -> bool:
    """
    A simple function that converts an str value to bool and returns it.

    ### Parameters:
    ---
    value : str
        The value that will be converted.
    
    ### Returns:
    ---
    bool
        Converted value.
    """
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False


def show_error_message(message: str) -> None:
    """
    Function to show that an error occured.

    ### Parameters:
    ---
    message : str
        Error message.
    """
    root = tk.Tk()
    root.withdraw() 
    messagebox.showerror("HATA", message)
    root.destroy()


def settings_reader(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def capture(camera, show_frame, capture_duration=10):
    global running
    cap = cv2.VideoCapture(camera)
    
    if not cap.isOpened():
        message = f"{camera} numaralı kamera açılamadı. Bu kameranın sistemde var olduğuna emin olun."
        show_error_message(message)
        running = False
        return

    start_time = time.time()

    while time.time() - start_time < capture_duration and running:
        ret, frame = cap.read()
        if not ret:
            message = f"{camera} numaralı kamera şu anda kullanımda veya başka bir hata oluştu."
            show_error_message(message)
            running = False 
            break
        
        rgb_frame = frame[:, :, ::-1]  # BGR to RGB conversion
        face_locations = face_recognition.face_locations(rgb_frame)

        # recognition part??
        
        if show_frame:
            for top, right, bottom, left in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.imshow('Webcam', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): # for debugging purposes
                break

    cap.release()
    if show_frame:
        cv2.destroyAllWindows()


def capture_callback():
    global running
    if not running:  
        return
    
    settings = settings_reader('settings.json')
    camera = settings['camera']
    show_frame = str_to_bool(settings['show_frame']) # exception handling
    capture(camera, show_frame)
    if running:  
        sleep_time = 30  
        elapsed = 0
        while running and elapsed < sleep_time:  
            time.sleep(1)  
            elapsed += 1
        if running:  
            threading.Timer(30, capture_callback).start()


if __name__ == '__main__':
    capture_callback()
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        print("Program terminated.")