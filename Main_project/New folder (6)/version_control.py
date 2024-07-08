import pygame
from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy as np
import simpleaudio as sa
from twilio.rest import Client
import geocoder



count = 0

account_sid = 'AC5606b2e0beb80dc5f42f1fae0998b3e2'
auth_token = '4bf0bcf3a6a36ccf956cb60b9157958e'

client = Client(account_sid, auth_token)

wave_obj = sa.WaveObject.from_wave_file("alarmbuzz.wav")

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    A = distance.euclidean(mouth[2], mouth[10])
    B = distance.euclidean(mouth[4], mouth[8])
    mar = B / A
    return mar

thresh_ear = 0.25
thresh_mar = 0.5  
frame_check = 20
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS['mouth']

pygame.mixer.init()

cap = cv2.VideoCapture(0)
flag = 0
alert_timer = 0
drowsy_count = 0
is_playing_alarm = False

def play_alarm():
    global is_playing_alarm
    if not is_playing_alarm:
        global count
        count += 1
        is_playing_alarm = True
        wave_obj.play()  

def stop_alarm():
    global is_playing_alarm
    if is_playing_alarm:
        is_playing_alarm = False
        pygame.mixer.stop()  

while True:
    ret, frame = cap.read()
    frame = imutils.resize(frame, width=800)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    subjects = detect(gray, 0)

    for subject in subjects:
        shape = predict(gray, subject)
        shape = face_utils.shape_to_np(shape)
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        mouth = shape[mStart:mEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        mar = mouth_aspect_ratio(mouth)

        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        mouthHull = cv2.convexHull(mouth)

        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)

        if leftEAR < thresh_ear and rightEAR < thresh_ear:
            flag += 1
            if flag >= frame_check:
                alert_timer += 1
                if alert_timer == 1:  
                    play_alarm()

                if alert_timer >= 5:  
                    drowsy_count += 1
                    if drowsy_count == 4:
                        cv2.putText(frame, "TAKE REST", (frame.shape[1] // 2 - 100, frame.shape[0] // 2),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                    try:
                        location=geocoder.ip('me')
                        latitude=location.lat
                        longitude=location.lat
                        location_name=location.address
                        message_body = f'Driver is Showing Drowsiness Sign: \n\n\t\tCurrent Location: Lat {latitude}, \n\n\t\tLong {longitude}, \n\n\t\tCurrent place: {location_name}'
                        message = client.messages.create(
                            from_='whatsapp:+14155238886',
                            body=message_body,
                            to='whatsapp:+919226038185'
                        )
                    except Exception as e:
                        print("An error occurred:", e)

        else:
            flag = 0
            alert_timer = 0
            stop_alarm()  

        if mar > thresh_mar and mar < 0.9:  # Adjusted threshold to avoid false positives
            cv2.putText(frame, "Yawning", (subject.left(), subject.top() - 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 255), 2)
            try:
                location=geocoder.ip('me')
                latitude=location.lat
                longitude=location.lng
                location_name=location.address
                message_body = f'Driver is Showing Drowsiness Sign: \n\n\t\tCurrent Location: Lat {latitude}, \n\n\t\tLong {longitude}, \n\n\t\tCurrent Place: {location_name}'

                message = client.messages.create(
                    from_='whatsapp:+14155238886',
                    body=message_body,
                    to='whatsapp:+919226038185'
                )
            except Exception as e:
                print("An error occurred:", e)

    cv2.putText(frame, f"Score: {flag}", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

pygame.mixer.quit()
cv2.destroyAllWindows()
cap.release()

print(f"Drowsiness detected {count} times")
