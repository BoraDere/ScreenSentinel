# # import pstats
# # p = pstats.Stats('restats')
# # p.strip_dirs().sort_stats(-1).print_stats()

# import tkinter as tk
# from tkinter import simpledialog
# import cv2

# def list_cameras(max_checks=10):
#     """Attempt to open cameras up to a max index to check which are available."""
#     available_cameras = []
#     for i in range(max_checks):
#         cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
#         if cap.isOpened():
#             available_cameras.append(i)
#             cap.release()
#         else:
#             break  # Stop checking if one index is not available
#     return available_cameras

# def ask_camera_selection(available_cameras):
#     """Create a Tkinter dialog to select a camera."""
#     def on_select():
#         selected_index.set(available_cameras[cameras_listbox.curselection()[0]])
#         root.destroy()

#     root = tk.Tk()
#     root.title("Select Camera")
#     selected_index = tk.IntVar(value=available_cameras[0])  # Default to the first camera

#     cameras_listbox = tk.Listbox(root)
#     cameras_listbox.pack()

#     for camera in available_cameras:
#         cameras_listbox.insert(tk.END, f"Camera {camera}")

#     select_button = tk.Button(root, text="Select", command=on_select)
#     select_button.pack()

#     root.mainloop()
#     return selected_index.get()

# # Example usage
# available_cameras = list_cameras()
# selected_camera_index = ask_camera_selection(available_cameras)
# print(f"Selected Camera Index: {selected_camera_index}")

# from pygrabber.dshow_graph import FilterGraph

# graph = FilterGraph()
# print(graph.get_input_devices())

import subprocess
import tkinter as tk
from tkinter import simpledialog
import cv2

def list_cameras_with_powershell():
    """List camera devices using PowerShell and map them to indices."""
    command = ["powershell", "-Command", "Get-CimInstance Win32_PnPEntity | ? { $_.service -eq 'usbvideo' } | Select-Object -Property Name"]
    result = subprocess.run(command, capture_output=True, text=True)
    
    camera_names = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    camera_names.remove('Name')
    camera_names.remove('----')
    
    return camera_names

def list_cameras(max_checks=10):
    """Attempt to open cameras up to a max index to check which are available."""
    available_cameras = []
    for i in range(max_checks):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def ask_camera_selection(camera_names):
    """Create a Tkinter dialog to select a camera by name."""
    def on_select():
        selected_index.set(camera_names.index(cameras_listbox.get(cameras_listbox.curselection())))
        root.destroy()

    root = tk.Tk()
    root.title("Select Camera")
    selected_index = tk.IntVar(value=0)  # Default to the first camera

    cameras_listbox = tk.Listbox(root)
    cameras_listbox.pack()

    for name in camera_names:
        cameras_listbox.insert(tk.END, name)

    select_button = tk.Button(root, text="Select", command=on_select)
    select_button.pack()

    root.mainloop()
    return selected_index.get()

# Example usage
camera_names = list_cameras_with_powershell()
selected_camera_index = ask_camera_selection(camera_names)
print(f"Selected Camera: {camera_names[selected_camera_index]}")

# Assuming the order of cameras listed by PowerShell matches the order used by OpenCV
opencv_camera_index = list_cameras()[selected_camera_index]
print(f"OpenCV Camera Index: {opencv_camera_index}")

# import subprocess

# command = ["powershell", "-Command", "Get-CimInstance Win32_PnPEntity | ? { $_.service -eq 'usbvideo' } | Select-Object -Property Name"]
# result = subprocess.run(command, capture_output=True, text=True)
# camera_names = [line.strip() for line in result.stdout.split('\n') if line.strip()]
# camera_names.remove('Name')
# camera_names.remove('----')
# print(camera_names)

# import subprocess
# import tkinter as tk
# from tkinter import simpledialog
# import cv2

# def list_cameras_with_powershell():
#     """List camera devices using PowerShell and map them to indices."""
#     command = ["powershell", "-Command", "Get-CimInstance Win32_PnPEntity | ? { $_.service -eq 'usbvideo' } | Select-Object -Property Name"]
#     result = subprocess.run(command, capture_output=True, text=True)
    
#     camera_names = [line.strip() for line in result.stdout.split('\n') if line.strip()]
#     camera_names.remove('Name')
#     camera_names.remove('----')
    
#     return camera_names


# def list_cameras(max_checks=10):
#     """Attempt to open cameras up to a max index to check which are available."""
#     available_cameras = []
#     for i in range(max_checks):
#         cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
#         if cap.isOpened():
#             available_cameras.append(i)
#             cap.release()
#     return available_cameras