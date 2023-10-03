import numpy as np
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
import base64
import socketio
import time
import pickle
import os
import webbrowser
from natsort import natsorted
import subprocess
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
import mysql.connector as msq
from sqlalchemy import create_engine

cd = os.getcwd()
cd = os.path.join(cd, "img")
n = 0

for filename in os.listdir(cd):
    if filename.endswith(".jpg"):
        file_path = os.path.join(cd, filename)
        os.remove(file_path)

sio = socketio.Client()
cap=cv2.VideoCapture('video2.mp4')
tracker = DeepSort(max_age=1)
cord = [239, 661, 241, 291]
x1,x2,y1,y2 = cord

def count_jpg_files(directory_path):
    jpg_files = [filename for filename in os.listdir(directory_path) if filename.lower().endswith(".jpg")]
    return jpg_files

def delete_images(directory_path, image_files):
    sorted_images = natsorted(image_files)
    images_to_delete = sorted_images[:len(sorted_images) - 5] 
    for image in images_to_delete:
        image_path = os.path.join(directory_path, image)
        os.remove(image_path)

def send_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    encoded_frame = base64.b64encode(buffer).decode('utf-8')
    sio.emit('main', {'frame': encoded_frame})

def Center(x1,y1,x2,y2):
    x = int((x1 + x2)/2)
    y = int((y1 + y2)/2)
    return x,y

def TrackCars(frame,lst):
    bbox_id = tracker.update_tracks(lst, frame=frame)
    lst1 = []
    for bbox in bbox_id:
        if not bbox.is_confirmed():
            continue
        id = bbox.track_id
        xx1,yy1,xx2,yy2 = bbox.to_ltrb()
        xx1,yy1,xx2,yy2 = int(xx1),int(yy1),int(xx2/1.8),int(yy2/1.8)
        cx, cy = Center(xx1,yy1,xx2,yy2)
        lst1.append([cx,cy,id])
        frame = cv2.circle(frame,(cx,cy),4,(0,0,255),-1)
        frame = cv2.putText(frame,str(id),(cx,cy),cv2.FONT_HERSHEY_COMPLEX,0.4,(0,255,255),1)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
    cv2.putText(frame,str(count),(100,50),cv2.FONT_HERSHEY_COMPLEX,0.8,(255,0,0),2)
    global n
    n = n + 1
    global cd
    imgd = os.path.join(cd, f'{n}.jpg')
    cv2.imwrite(imgd, frame)
    jpg_files = count_jpg_files(cd)
    if len(jpg_files) > 5:
        delete_images(cd, jpg_files)
    lst1 = np.array(lst1)
    return lst1.astype(int)

def Counter(ids, lstid):
    count = 0
    for i in lstid:
        if i not in ids:
            count = count + 1
    return count

def IndexProcess(lst):
    if np.any(lst):
        cond = lst[:, 0] > x1
        lst = lst[cond]
        cond = lst[:, 0] < x2
        lst = lst[cond]
        cond = lst[:, 1] > y1
        lst = lst[cond]
        cond = lst[:, 1] < y2
        lst = lst[cond]
        lstid = (lst[:,2]).tolist()
        return lstid
    else:
        return []

def Table(count, table_name, engine):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, con=engine)
    dt = df['date'].tolist()
    current_date = datetime.now().date()
    if current_date not in dt:
        count = 0
        insert_query = f"INSERT INTO {table_name} (date, count) VALUES (%s, %s)"
        cursor.execute(insert_query, (current_date, count))
        connection.commit()
    update_query = f"UPDATE {table_name} SET count = %s WHERE date = %s"
    cursor.execute(update_query, (count, current_date))
    connection.commit()
    return count

@sio.on('connect')
def on_connect():
    print('Connected to server')
    sio.emit('svr', 'ok')

frm = ''
@sio.on('frame')
def frame(concent):
    ret,frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame,(1020,500))
    send_frame(frame)
    global frm
    frm = frame


host = 'localhost'
user = 'username'
password = 'password'

connection = msq.connect(host=host,
                   user=user,
                   password=password,
                   database=user)

cursor = connection.cursor(buffered=True)
engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{user}')
current_date = datetime.now().date()
table_name = user
query = f"SELECT * FROM {table_name}"
df = pd.read_sql(query, con=engine)
dt = df['date'].tolist()

count = 0
if current_date not in dt:
    insert_query = f"INSERT INTO {table_name} (date, count) VALUES (%s, %s)"
    cursor.execute(insert_query, (current_date, count))
    connection.commit()
else:
    query = f"SELECT count FROM {table_name} WHERE date = %s"
    cursor.execute(query, (current_date,))
    count = cursor.fetchone()
    count = int(count[0])
    cursor = connection.cursor()

ids = []
@sio.on('calc')
def calc(lst):
    global ids, count, df, current_date, dt, table_name, engine
    count = Table(count, table_name, engine)
    lst = pickle.loads(lst)
    lst = TrackCars(frm, lst)
    lstid = IndexProcess(lst)
    count = count + Counter(ids, lstid)
    ids = ids + lstid
    if len(ids) > 20:
        ids = ids[-20:]
    frame('ok')

sio.connect('http://localhost:5000')
sio.wait()
