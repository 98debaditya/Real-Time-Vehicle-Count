import cv2
import numpy as np
from mlsocket import MLSocket
from ultralytics import YOLO
from tracker import*
from deep_sort_realtime.deepsort_tracker import DeepSort
from signal import signal, SIGPIPE, SIG_DFL  
signal(SIGPIPE,SIG_DFL)
import concurrent.futures

print('please wait')

def VehicleList(df, model):
    df = model.predict(df)
    df = df[0].boxes.data
    df = df.numpy()
    df = df.astype(np.int32)
    lst=[]
    for i in range(df.shape[0]):
        x1,y1,x2,y2,s,d = df[i]
        if d==2 or d==5 or d==7 or d==1 or d==3:
            lst.append(([x1,y1,x2,y2],s,d))
    return lst    

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
        x1,y1,x2,y2 = bbox.to_ltrb()
        x1,y1,x2,y2 = int(x1),int(y1),int(x2/1.8),int(y2/1.8)
        cx, cy = Center(x1,y1,x2,y2)
        lst1.append([cx,cy,id])
    lst1 = np.array(lst1)
    return lst1.astype(int)

def Counter(ids, lstid):
    count = 0
    for i in lstid:
        if i not in ids:
            count = count + 1
    return count

def IndexProcess(lst,x1,x2,y1,y2):
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

def NewCell(conn, addr):
    _PORT_ = addr[1]
    count=0
    ids = []
    cord = conn.recv(_PORT_)
    print(cord)
    x1,x2,y1,y2 = cord
    while True:
        frame = conn.recv(_PORT_)
        conn.send(np.array([count]))
        lst = VehicleList(frame, model)
        lst = TrackCars(frame, lst)
        lstid = IndexProcess(lst,x1,x2,y1,y2)
        count = count + Counter(ids, lstid)
        ids = ids + lstid
        if len(ids) > 200:
            ids = ids[-200:]

    conn.close()
    s.close()

if __name__ == '__main__':
    model=YOLO('yolov8l.pt')
    print('Ready to connect')
    tracker = DeepSort(max_age=5)
    HOST='127.0.0.1'
    PORT=9930
    s=MLSocket()
    s.bind((HOST,PORT))
    s.listen(10)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            conn, addr = s.accept()
            print(addr)
            executor.submit(NewCell, conn, addr)
        s.close()
