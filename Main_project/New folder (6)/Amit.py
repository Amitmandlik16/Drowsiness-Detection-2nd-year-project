import pygame
from flask import Flask
from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy as np
import simpleaudio as sa
from twilio.rest import Client
import geocoder
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime

# Define Flask app and database configurations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///drowsy.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define Drowsy database model
class drowsy(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer())
    driver_name = db.Column(db.String(60))
    v_start = db.Column(db.DateTime)
    v_stop = db.Column(db.DateTime)
    time = db.Column(db.DateTime)
    d_type = db.Column(db.String(10))
    d_total_time = db.Column(db.Integer)
    location = db.Column(db.String(100))

# Define global variables and configurations
v_started = datetime.now()
count = 0
account_sid = 'AC5606b2e0beb80dc5f42f1fae0998b3e2'
auth_token = '4bf0bcf3a6a36ccf956cb60b9157958e'
client = Client(account_sid, auth_token)
wave_obj = sa.WaveObject.from_wave_file("alarmbuzz.wav")

# Define eye and mouth aspect ratio functions
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    
    A = distance.euclidean(mouth[2], mouth[10])  
    B = distance.euclidean(mouth[4], mouth[8])  
    C = distance.euclidean(mouth[0], mouth[6])  

    mar = (A + B) / (2.0 * C)

    return mar

# Setting thresholds
thresh_ear = 0.25
thresh_mar = 0.5  
frame_check = 20
yawn_duration = 0

# Initialize face detector and shape predictor
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS['mouth']

pygame.mixer.init()

# Start video capture
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
                        longitude=location.lng
                        location_name=location.address
                        message_body = f'Driver is Showing Drowsiness Sign: \n\n\t\tCurrent Location: Lat {latitude}, \n\n\t\tLong {longitude}, \n\n\t\tCurrent place: {location_name}'
                        message = client.messages.create(
                            from_='whatsapp:+14155238886',
                            body=message_body,
                            to='whatsapp:+919226038185'
                        )
                    except Exception as e:
                        print("An error occurred:", e)

                    now=datetime.now();
                    with app.app_context():
                        Drowsy = drowsy(driver_id=3, driver_name="Amit", v_start=v_started,v_stop=now,time=now,d_type="eyes",d_total_time=5,location=location.address)
                        db.session.add(Drowsy)
                        db.session.commit()

        else:
            flag = 0
            alert_timer = 0
            stop_alarm()  

        if mar > thresh_mar:  # Check if mouth aspect ratio indicates yawning
            if yawn_duration == 0:
                yawn_start = datetime.now()
            yawn_duration = (datetime.now() - yawn_start).total_seconds()
            if yawn_duration >= 3:
                # Set variables here for yawning more than 3 seconds
                print("Yawning for more than 3 seconds")
            cv2.putText(frame, "Yawning", (subject.left(), subject.top() - 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 255), 2)
            play_alarm()
            try:
                location=geocoder.ip('me')
                latitude=location.lat
                longitude=location.lng
                location_name=location.address
                message_body = f'Driver is Showing Yawning Sign: \n\n\t\tCurrent Location: Lat {latitude}, \n\n\t\tLong {longitude}, \n\n\t\tCurrent Place: {location_name}'

                message = client.messages.create(
                    from_='whatsapp:+14155238886',
                    body=message_body,
                    to='whatsapp:+919226038185'
                )
            except Exception as e:
                print("An error occurred:", e)
            stop_alarm()

            now=datetime.now();
            with app.app_context():
                Drowsy = drowsy(driver_id=3, driver_name="Amit", v_start=v_started,v_stop=now,time=now,d_type="yawn",d_total_time=5,location=location.address)
                db.session.add(Drowsy)
                db.session.commit()

    cv2.putText(frame, f"Score: {flag}", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        v_stopped=datetime.now()
        with app.app_context():
            records_to_update = drowsy.query.filter_by(v_start=v_started).all()
            for record in records_to_update:
                record.v_stop = v_stopped
            db.session.commit()
        break

    if key == ord("a"):
        try:
            location = geocoder.ip('me')
            latitude = location.latlng[0]
            longitude = location.latlng[1]
            location_name = location.address
            message_body = f'sorry to inform Driver Id 3 is involved in accident: \n\n\t\tCurrent Location: Lat {latitude}, \n\n\t\tLong {longitude}, \n\n\t\tCurrent place: {location_name}'
            message=client.messages.create(                        
                from_='whatsapp:+14155238886',
                body=message_body,
                to='whatsapp:+919226038185'
            )        
        except Exception as e:
            print("Error occured: ",e)
        now=datetime.now();
        with app.app_context():
            Drowsy = drowsy(driver_id=3, driver_name="Amit", v_start=v_started,v_stop=now,time=now,d_type="Accident",d_total_time=0,location="sangamner")
            db.session.add(Drowsy)
            db.session.commit()

pygame.mixer.quit()
cv2.destroyAllWindows()
cap.release()

print(f"Drowsiness detected {count} times")
