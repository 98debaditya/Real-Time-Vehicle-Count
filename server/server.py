import numpy as np
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
import cv2
import pandas as pd
from ultralytics import YOLO
import base64
import pickle
from flask_cors import CORS
from sqlalchemy import create_engine
import mysql.connector as msq
import os

app = Flask(__name__)
CORS(app)
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

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/table/<user>')
def show_table(user):
    temp = f'{user}temp.csv'
    df = pd.read_csv(temp)
    cd = os.getcwd()
    os.remove(os.path.join(cd, temp))
    return render_template('table.html', table=df.to_html(index=False))

@socketio.on('login')
def handle_login(data):
    try:
        user = data['username']
        password = data['password']
        table_name = user
        host = 'localhost'
        mydb = msq.connect(host=host, user=user, password=password)
        cur = mydb.cursor()
        mydb.database = user
        engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{user}')
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, con=engine)
        df.to_csv(f'{user}temp.csv',index=False)
        emit('login_status', {'status': 'success', 'user':user})
    except:
        emit('login_status', {'status': 'failure'})

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
