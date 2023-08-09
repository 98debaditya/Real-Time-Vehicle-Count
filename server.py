import numpy as np
from flask import Flask, request
from flask_socketio import SocketIO, emit
import cv2
from ultralytics import YOLO
import base64
import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, async_mode='eventlet')
model=YOLO('yolov8l.pt')
print('server rady')

def receive_frame(frame):
    frame = base64.b64decode(frame['frame'])
    frame = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
    return frame

def VehicleList(df,model):
    df = model.predict(df)
    df = df[0].boxes.data
    df = df.numpy()
    df = df.astype(np.int32)
    lst=[]
    for i in range(df.shape[0]):
        x1,y1,x2,y2,s,d = df[i]
        if d==2 or d==5 or d==7 or d==1 or d==3:
            lst.append([[x1,y1,x2,y2],s,d])
    return lst

@socketio.on('svr')
def Concent(concent):
    emit('frame', 'ok')

@socketio.on('main')
def MAIN(frame):
    frame = receive_frame(frame)
    lst = VehicleList(frame, model)
    lst = pickle.dumps(lst)
    emit('calc', lst)

if __name__ == '__main__':
    socketio.run(app)
