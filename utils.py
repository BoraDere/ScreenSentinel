import json
import cv2
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import sys
import os
from datetime import datetime
import subprocess
import constants


###################################### FUNCTIONS ######################################


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


#######################################################################################


def logger(log: str, type: str) -> None:
    with open('logs.txt', 'a') as w:
        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        w.write(f'[{dt}] {type}: {log}\n')


#######################################################################################


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


#######################################################################################


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


#######################################################################################


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


#######################################################################################


def list_cameras(max_checks=10):
    available_cameras = []
    for i in range(max_checks):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras


#######################################################################################


def list_cameras_with_powershell():
    command = ["powershell", "-Command", "Get-CimInstance Win32_PnPEntity | ? { $_.service -eq 'usbvideo' } | Select-Object -Property Name"]
    result = subprocess.run(command, capture_output=True, text=True)
    
    camera_names = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    camera_names.remove('Name')
    camera_names.remove('----')
    
    return camera_names


#######################################################################################


def ask_user_name():
    root = tk.Tk()
    root.withdraw()  

    user_name = simpledialog.askstring("Name", "Please enter your name:")
    
    root.destroy()
    
    return user_name


#######################################################################################


def check_authorized_users(user_image_count: int):
    """
    This function is intended to run only in the case which there is no authorized_users folder is prepared before the initial run of the code,
    which is actually opposite of the advised usage. 
    MUST CLARIFY THE ACTUAL USAGE SCENARIOS
    """
    if not os.path.exists(constants.AUTHORIZED_USERS_DIR):
        os.makedirs(constants.AUTHORIZED_USERS_DIR)
        user_name = ask_user_name()
        user_dir = os.path.join(constants.AUTHORIZED_USERS_DIR, user_name)
        os.makedirs(user_dir)

        # camera selection part
        camera_names = list_cameras_with_powershell()
        selected_camera_index = ask_camera_selection(camera_names)
        # TESTTTT
        opencv_camera_index = list_cameras()[selected_camera_index]

        with open('settings.json', 'r') as f:
            data = json.load(f)

        data['camera'] = opencv_camera_index

        with open('settings.json', 'w') as w:
            json.dump(data, w)

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