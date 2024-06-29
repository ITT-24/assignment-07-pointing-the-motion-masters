import cv2
import mediapipe as mp
import pyautogui
from pynput.mouse import Button, Controller

#
# hand motion detection for cursor movement:
# show hand to webcam like you would high five, move around to move mouse, to click touch palm with middle, index and
# pinky finger while keeping index finger straight
# basic structure and normalized coordinates generated with chatGPT
#
#setup videoCapture ID before starting programm
cap = cv2.VideoCapture(1)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_drawing = mp.solutions.drawing_utils
mouse = Controller()
interpolation_factor = 0.2
# Store previous cursor position for interpolation
prev_cursor_x, prev_cursor_y = pyautogui.position()


# Function to convert normalized landmarks to pixel coordinates #chatgpt
def normalized_to_pixel_coordinates(normalized_landmark, image_width, image_height):
    return int(normalized_landmark.x * image_width), int(normalized_landmark.y * image_height)

while True:

    # Read a frame from the camera
    ret, frame = cap.read()
    if not ret:
       # break
        print("Failed to grab frame")


    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_height, image_width, _ = frame.shape
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            #get finger coordinates
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]

            # Convert normalized coordinates to pixel coordinates
            index_x, index_y = normalized_to_pixel_coordinates(index_finger_tip, image_width, image_height)
            middle_tip_x, middle_tip_y = normalized_to_pixel_coordinates(middle_finger_tip, image_width, image_height)
            middle_mcp_x, middle_mcp_y = normalized_to_pixel_coordinates(middle_finger_mcp, image_width, image_height)

            # Calculate the screen cursor position based on index finger position
            screen_width, screen_height = pyautogui.size()
            cursor_x = index_x * screen_width / image_width
            cursor_y = index_y * screen_height / image_height

            # Interpolate cursor position for smoothing
            interpolated_x = int(prev_cursor_x + interpolation_factor * (cursor_x - prev_cursor_x))
            interpolated_y = int(prev_cursor_y + interpolation_factor * (cursor_y - prev_cursor_y))

            # Move the cursor to the interpolated position
            pyautogui.moveTo(interpolated_x, interpolated_y)

            # Update previous cursor position
            prev_cursor_x, prev_cursor_y = interpolated_x, interpolated_y

            # left mouse button clicked when middle finger touches palm, easier when ring finger and pinky also touch
            if middle_tip_y > middle_mcp_y:
                pyautogui.click(button='left')

