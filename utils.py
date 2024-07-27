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
import shutil
from send2trash import send2trash


###################################### FUNCTIONS ######################################


def lock_screen() -> None:
    """
    A really simple function to lock the screen.
    """
    os.system("rundll32.exe user32.dll,LockWorkStation")


#######################################################################################


def save_image_to_user_directory(frame: cv2.numpy.ndarray, user_name: str) -> None:
    """
    Function that saves the image taken with the format of f"{user_name}_{dt}.jpg"

    Args:
        frame(numpy.ndarray): Captured frame at that moment.
        user_name(str): User name.
    """
    user_dir = os.path.join(constants.AUTHORIZED_USERS_DIR, user_name)

    # Using datetime so all images can have unique names
    dt = datetime.now().strftime("%d%m%Y_%H%M%S")

    photo_path = os.path.join(user_dir, f"{user_name}_{dt}.jpg")
    cv2.imwrite(photo_path, frame)


#######################################################################################


def delete_images() -> None:
    """
    Function that deletes all images added latterly.
    """
    for user_dir in os.listdir(constants.AUTHORIZED_USERS_DIR):
        user_path = os.path.join(constants.AUTHORIZED_USERS_DIR, user_dir)
        for user_image in os.listdir(user_path):
            # Should not delete initial images because they tend to be the best ones
            if 'init' not in user_image:
                image_path = os.path.join(user_path, user_image)
                send2trash(image_path)


#######################################################################################


def check_count_limit(count_limit: int) -> bool:
    """
    Function that checks if the count limit is reached.

    Args:
        count_limit(int): Image count limit per user, defined in the settings file.

    Returns:
        True if one user has reached the limit.
        Else, False.
    """
    for user_dir in os.listdir(constants.AUTHORIZED_USERS_DIR):
        user_path = os.path.join(constants.AUTHORIZED_USERS_DIR, user_dir)
        user_length = len(os.listdir(user_path))
        if user_length == count_limit:
            shutil.rmtree(constants.AUTHORIZED_ENCODINGS_DIR)
            return True
    return False


#######################################################################################


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
        message = 'Settings file cannot be found. It must be named as "settings" and the file format must be JSON.'
        logger(message, 'ERROR')
        sys.exit()


#######################################################################################


def logger(log: str, type: str) -> None:
    """
    Function that does the logging processes.

    Args:
        log(str): Logging information.
        type(str): Logging type.
    """
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


def str_to_bool(value: str) -> (bool | None):
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


def ask_camera_selection(camera_names: list) -> int:
    """
    Function that lists available cameras.

    Args:
        camera_names(list): Available camera names.

    Returns:
        (int): Index of the selected camera.
    """
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


def list_cameras(max_checks=10) -> list:
    """
    Function to check all available cameras. This cannot be easily done on Python, so this is a runaround 
    that checks if the camera with the selected index returns anything in the amount of max_checks.

    Args:
        max_checks(int): Upper limit of checks.

    Returns:
        (list): List of available camera indices.
    """
    available_cameras = []
    for i in range(max_checks):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        # This means there is a camera installed with this index
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras


#######################################################################################


def list_cameras_with_powershell() -> list:
    """
    Function that gets available camera names using a powershell command as a subprocess.

    Returns:
        (list): List of available camera names.
    """
    command = ["powershell", "-Command", "Get-CimInstance Win32_PnPEntity | ? { $_.service -eq 'usbvideo' } | Select-Object -Property Name"]
    result = subprocess.run(command, capture_output=True, text=True)
    
    camera_names = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    camera_names.remove('Name')
    camera_names.remove('----')
    
    return camera_names


#######################################################################################


def ask_user_name() -> str:
    """
    Function that asks for a user name.

    Returns:
        (str): User name.
    """
    root = tk.Tk()
    root.withdraw()  

    user_name = simpledialog.askstring("Name", "Please enter your name:")
    
    root.destroy()
    
    return user_name


#######################################################################################


def check_authorized_users(user_image_count: int) -> None:
    """
    This function is intended to run only in the case which there is no authorized_users folder is prepared before the initial run of the code,
    which is actually opposite of the advised usage. 
    MUST CLARIFY THE ACTUAL USAGE SCENARIOS

    Args:
        user_image_count(int): Amount of images that the user is asked to take.
    """
    if not os.path.exists(constants.AUTHORIZED_USERS_DIR):
        os.makedirs(constants.AUTHORIZED_USERS_DIR)
        user_name = ask_user_name()
        user_dir = os.path.join(constants.AUTHORIZED_USERS_DIR, user_name)
        os.makedirs(user_dir)

        # Camera selection part
        camera_names = list_cameras_with_powershell()
        selected_camera_index = ask_camera_selection(camera_names)
        opencv_camera_index = list_cameras()[selected_camera_index]

        with open('settings.json', 'r') as f:
            data = json.load(f)

        data['camera'] = opencv_camera_index

        with open('settings.json', 'w') as w:
            json.dump(data, w)

        cap = cv2.VideoCapture(opencv_camera_index)

        # Capture photo
        for i in range(user_image_count):
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger("Failed to capture image", "ERROR")
                    break
                cv2.imshow('Capture Photo', frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('s'):
                    # Save photo
                    photo_path = os.path.join(user_dir, f"{user_name}_init_{i+1}.jpg")
                    cv2.imwrite(photo_path, frame)
                    logger(f"Photo saved: {photo_path}", "INFO")
                    break  
                elif key == ord('q'):  # to quit
                    break

            if key == ord('q'):  
                break

        cap.release()
        cv2.destroyAllWindows()