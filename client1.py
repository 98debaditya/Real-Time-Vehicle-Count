import cv2
import numpy as np
from mlsocket import MLSocket
from signal import signal, SIGPIPE, SIG_DFL  
signal(SIGPIPE,SIG_DFL)

cap=cv2.VideoCapture('video2.mp4')
s = MLSocket()
s.connect(('127.0.0.1',9931))

cord = np.array([239, 661, 241, 291])

x1,x2,y1,y2 = cord
s.send(cord)

while True:
    ret,frame = cap.read()
    frame = cv2.resize(frame, (1020,500))
    s.send(frame)
    count = s.recv(1024)
    cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
    cv2.putText(frame,'Total = ' + str(count),(100,50),cv2.FONT_HERSHEY_COMPLEX,0.8,(255,0,0),2)
    cv2.imshow('frame',frame)
    key = cv2.waitKey(1)
    if (key == 27) or (key == 113):
        break

s.close()
