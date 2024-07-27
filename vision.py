import cv2
import face_recognition
import time
import sys
from concurrent.futures import ProcessPoolExecutor
import os
import pickle
from utils import logger, show_error_message, check_count_limit, delete_images, lock_screen, save_image_to_user_directory
import constants

######################################## FLAGS ########################################

running = True
process_current_frame = True
first_run = True

###################################### FUNCTIONS ######################################


def encode_face(face_image) -> list | None:
    """
    Function to encode faces using face_recognition.

    Args:
        face_image(cv2 frame): Cropped face image.

    Returns:
        encodings: Face encoding if face_encodings didn't return None, else None.
    """
    # Using hog model to increase the performance a bit
    encodings = face_recognition.face_encodings(face_image, model='hog')

    if encodings:
        return encodings[0]
    else:
        return None


#######################################################################################


def load_or_generate_encodings() -> dict:
    """
    The function that checks if authorized_encodings dictionary should be loaded or generated.
    """
    authorized_encodings = {}

    # If path exists load data from files
    if os.path.exists(constants.AUTHORIZED_ENCODINGS_DIR):
        for user_dir in os.listdir(constants.AUTHORIZED_ENCODINGS_DIR):
            user_encodings = []
            user_path = os.path.join(constants.AUTHORIZED_ENCODINGS_DIR, user_dir)

            for encoding_file in os.listdir(user_path):
                with open(os.path.join(user_path, encoding_file), 'rb') as f:
                    encoding = pickle.load(f)
                    user_encodings.append(encoding)

            authorized_encodings[user_dir] = user_encodings

    # Else, create the directory and write encoding files       
    else:
        os.makedirs(constants.AUTHORIZED_ENCODINGS_DIR, exist_ok=True)
        for user_dir in os.listdir(constants.AUTHORIZED_USERS_DIR):
            user_path = os.path.join(constants.AUTHORIZED_USERS_DIR, user_dir)
            user_encodings_dir = os.path.join(constants.AUTHORIZED_ENCODINGS_DIR, user_dir)
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


#######################################################################################


def capture(camera: int, show_frame: bool, capture_duration: int, block_multi_user: bool, cap: cv2.VideoCapture, authorized_encodings: dict, count_limit: int) -> None:
    """
    Main function that is responsible of capturing, detecting and recognizing.

    Args:
        camera(int): ID of camera given in the settings file.
        show_frame(bool): Bool value of show_frame given in the settings file.
        capture_duration(int): Duration of capture in seconds.
        block_multi_user(bool): Setting states if the program should block multi user occurence.
        cap(cv2.VideoCapture): Capture variable.
        authorized_encodings(dict): Dictionary that consists encodings of authorized users.
        count_limit: Upper limit of photo amount per user.
    """
    global running, process_current_frame, first_run

    authorized_detected = False
    limit_reached = False
    
    # Error while opening the camera
    if not cap.isOpened():
        message = f"Camera {camera} cannot be used. Be sure that this device exists."
        logger(message, 'ERROR')
        show_error_message(message)
        sys.exit(message)

    start_time = time.time()
    user_names = []

    for user, encodings in authorized_encodings.items():
        user_names.extend([user] * len(encodings))

    if first_run:
        limit_reached = check_count_limit(count_limit)

        if limit_reached:
            authorized_encodings = load_or_generate_encodings()
            delete_images()

    while time.time() - start_time < capture_duration and running and not authorized_detected:
        
        ret, frame = cap.read()

        if not ret:
            # If cap.read() doesn't return a frame meaning there is a problem, which is mostly the camera being already used
            message = f"Camera {camera} is being used or another error occured."
            logger(message, 'ERROR')
            show_error_message(message)
            sys.exit(message)

        if process_current_frame:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)            
            rgb_small_frame = small_frame[:, :, ::-1]  # BGR to RGB conversion
            face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')

            # face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations, model='hog')
            faces = []
            for top, right, bottom, left in face_locations:
                if 0 <= top < bottom <= rgb_small_frame.shape[0] and 0 <= left < right <= rgb_small_frame.shape[1]:
                    face = rgb_small_frame[top:bottom, left:right]
                    faces.append(face)

            if faces:
                with ProcessPoolExecutor() as executor:
                    face_encodings = list(executor.map(encode_face, faces))
            else:
                face_encodings = []

            unauthorized_detected = False
            valid_face_encodings = [enc for enc in face_encodings if enc is not None]

            for encoding in valid_face_encodings:
                matches = face_recognition.compare_faces(
                    [enc for sublist in authorized_encodings.values() for enc in sublist], 
                    encoding, 
                    tolerance=constants.THRESHOLD,
                )

                if block_multi_user:
                    if not any(matches):
                        unauthorized_detected = True
                        break

                    if any(matches):
                        message = "Authorized person detected. Stopping capture."
                        logger(message, 'INFO')
                        if first_run and not limit_reached:
                            matched_user_index = matches.index(True)
                            matched_user_name = user_names[matched_user_index]
                            save_image_to_user_directory(frame, matched_user_name)
                            first_run = not first_run
                        authorized_detected = True
                        break  
                else:
                    if any(matches):  
                        message = "Authorized person detected. Stopping capture."  
                        logger(message, 'INFO')
                        if first_run and not limit_reached:
                            matched_user_index = matches.index(True)
                            matched_user_name = user_names[matched_user_index]
                            save_image_to_user_directory(frame, matched_user_name)
                            first_run = not first_run
                        authorized_detected = True
                        break

                    if not any(matches):
                        unauthorized_detected = True
                        break


            if unauthorized_detected:
                message = "Unauthorized person detected. System goes to sleep."
                logger(message, 'INFO')
                # running = False
                lock_screen()
                continue

            if show_frame:
                for top, right, bottom, left in face_locations:
                    top *= 4; right *= 4; bottom *= 4; left *= 4 
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.imshow('Webcam', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        process_current_frame = not process_current_frame 

    if not authorized_detected:
        message = "No authorized person detected. System goes to sleep."
        logger(message, 'INFO')
        lock_screen()

    # cap.release()
    if show_frame:
        cv2.destroyAllWindows()


#######################################################################################


def capture_loop(camera: int, show_frame: bool, wait_time: int, capture_duration: int, block_multi_user: bool, authorized_encodings: dict, count_limit: int):
    """
    Looping function for capture.
    
    Args:
        camera(int): ID of camera given in the settings file.
        show_frame(bool): Bool value of show_frame given in the settings file.
        wait_time(int): Time of sleeping in seconds.
        capture_duration(int): Duration of capture in seconds.
        block_multi_user(bool): Setting states if the program should block multi user occurence.
        authorized_encodings(dict): Dictionary that consists encodings of authorized users.
        count_limit: Upper limit of photo amount per user.
    """
    global running

    if not running:  
        return
    
    cap = cv2.VideoCapture(camera)
    
    while True:
        capture(camera, show_frame, capture_duration, block_multi_user, cap, authorized_encodings, count_limit)
        time.sleep(wait_time)