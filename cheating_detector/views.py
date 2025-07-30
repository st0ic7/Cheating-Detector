import cv2
import time
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from .models import Alert
import csv
import os
import threading
from playsound import playsound

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEEP_PATH = os.path.join(BASE_DIR, 'beep.mp3')

def play_beep():
    try:
        playsound(BEEP_PATH)
    except Exception as e:
        print("Audio error:", e)


# Load OpenCV Haar cascade once globally
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Global variable to hold the latest alert for frontend API
latest_alert = {
    'message': 'No alerts yet',
    'color': 'black'
}


def box_iou(boxA, boxB):
    # Calculate Intersection over Union between two boxes (x, y, w, h)
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    denom = float(boxAArea + boxBArea - interArea)
    iou = interArea / denom if denom != 0 else 0
    return iou

def save_alert(message):
    # Save alert to database and print for debugging
    Alert.objects.create(message=message, timestamp=timezone.now())
    print(f"Alert saved: {message}")

def gen_frames():
    cap = cv2.VideoCapture(0)
    prev_face_box = None
    iou_threshold = 0.5
    last_alert = None

    while True:
        success, frame = cap.read()
        if not success:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        faces = [(x*2, y*2, w*2, h*2) for (x, y, w, h) in faces]

        face_count = len(faces)

        if face_count == 0:
            alert = "student movement detected!"
            color = (0, 0, 255)
            prev_face_box = None
        elif face_count > 1:
            alert = "Multiple people detected!"
            color = (0, 0, 255)
            prev_face_box = None
        else:
            x, y, w, h = faces[0]
            current_box = (x, y, w, h)

            if prev_face_box is not None:
                iou = box_iou(prev_face_box, current_box)
                if iou < iou_threshold:
                    alert = "Student movement detected!"
                    color = (0, 0, 255)

                    # 🔊 Play beep sound in separate thread
                    play_beep()


                else:
                    alert = "Student detected"
                    color = (0, 255, 0)
            else:
                alert = "Student detected"
                color = (0, 255, 0)

            prev_face_box = current_box
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        if alert != last_alert:
            save_alert(alert)
            last_alert = alert

            latest_alert['message'] = alert
            latest_alert['color'] = 'red' if 'detected' in alert.lower() else 'green'

        cv2.putText(frame, alert, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(0.02)

    cap.release()


def webcam_feed(request):
    return StreamingHttpResponse(gen_frames(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

def home(request):
    return render(request, 'cheating_detector/webcam_feed.html')


from .models import Alert

def get_latest_alert(request):
    alert = Alert.objects.order_by('-timestamp').first()
    data = {'message': alert.message if alert else "No alerts yet"}
    return JsonResponse(data)


def export_alerts_csv(request):
    alerts = Alert.objects.all().order_by('-timestamp')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alerts_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Message'])

    for alert in alerts:
        writer.writerow([alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), alert.message])

    return response
