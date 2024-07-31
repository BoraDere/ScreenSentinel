# ScreenSentinel

ScreenSentinel is a simple program that tracks your webcam, detects anauthorized viewers and locks the system upon detection. It was designed for slow corporate devices mainly, that's why the main goal in this project was not affecting other processes in the system, rather than good visuals and best results.

It tracks the camera for a duration stated in the settings file, in periods of a certain time that is also stated in the settings. It detects faces and compares them with the ones defined as authorized, pre-run. Locks the screen upon detecting an unauthorized viewer, ensuring your discrete data will not be seen by any unwanted eyes.

It has a builtin logging system that logs important events with their dates and status. Throughout the usage, it takes pictures of authorized users and feeds it back to the dataset, keeping it updated. And it has customizable settings, making it adjustable for any scenario.

---

# Dependencies
Python 3.10 version was used developing this project. It is a stable, recommended version for OpenCV applications. Newer versions will probably work just fine, but no guarantees. 

To install dependencies, simply run:

```
pip install -r requirements.txt --use-feature=2020-resolver
```

Reslover is specifically used because NumPy 2.0 versions cause "Unsupported image type" errors with `dlib`. If this problem occurs, simply remove existing NumPy installation and install an older one:

```
pip uninstall numpy
```

```
pip install numpy==1.26.4
```

---

# Suggested Usage

Before initial run, keep in mind that you should not have a `authorized_user_encodings` folder, since this folder is for encodings and before initial run, you naturally cannot have any encodings prepared. Then, prepare a folder named `authorized_users` under the same directory, with this file hierarchy:
* authorized_users
* ├── user1
* │   ├── user1_init1.jpg
* │   └── user1_init2.jpg
* ├── user2
* │   ├── user2_init1.jpg
* │   ├── user2_init2.jpg
* │   └── user2_init3.jpg

All initially created images should have `init` in their name, since they will most likely the most quality photos. `init` states that these photos should not be deleted through the usage. 

If any initial photos are not provided, photo taking screen will appear. It will ask for a user name, then ask you to take photos for the amount stated in the settings file. Press `s` to take photos, and `q` to exit that screen, if you do not want to take more than 1 photos. As you can guess, at least 1 photo is necessary.

## Settings
* camera: Index of the camera will be used. 0 is the default value and states the primary camera. Data type must be integer.
* show_frame: States if the frame should be shown during process. This is for debugging only, default is False.
* count_limit: Maximum count limit for photos per user, before they get re-fed. Data type must be integer.
* block_multi_user: This setting states if the program should lock the screen when there is an unuthorized person detected, even though there is also an authorized person. Default is True and it is the suggested usage.
* user_image_count: Amount of photos the user is asked to take if there is no `authorized_users` folder prepared. Users are strongly suggested to prepare this folder before running the program.
* wait_time: This is the duration in seconds that the program will wait in between capturing processes. Data type must be integer.
* capture_duration: This is the capturing duration in seconds. Data type must be integer.

---

# Known Issues and Limitations
* As stated before, this was designed for slow machines mainly. If you enable `show_frame` and observe the capturing and recognizing system, video might (and probably will) struggle quite a bit.
* Since this project was part of my internship it is designed for Windows machines. Some functionalities will only work on Windows machines, thus whole program works only on Windows. Same functionalities can easily be implemented to work for other operating systems but this was simply not considered since it was not in the scope of my internship.
* For the same reason with the first point, this program uses a model ran on CPU. Which is actually the main reason of those struggles in the video. It may also cause some faulty detections, you can simply increase threshold for your convenience.
