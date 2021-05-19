#!/usr/bin/env python

from maya import cmds
from maya import OpenMayaUI as omui

from window_docker import Dock

# import the necessary packages
from imutils import face_utils

import dlib
import cv2
import os
import math
import time
from math import cos, sin, sqrt
import numpy as np

# Maya 2016 uses PySide and Maya 2017+ uses PySide2, so try PySide2 first before resorting to PySide
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtUiTools import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtUiTools import *
    from shiboken import wrapInstance

"""
        This experiment uses DLIB (dlib.net) and opencv (opencv.org) to track faces from a video stream
        and display them in a Qt window in maya.
        The tracked faces are roughly mapped to Victor's eyes.
        You need to have a Victor rig in the scene.
        by chris rogers 7/2018
        (C) Anki, Inc.
"""

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)

# these values correspond to the 68 face landmarks
# https://cdn-images-1.medium.com/max/1600/1*96UT-D8uSXjlnyvs9DZTog.png

rbrow = [17, 18, 19, 20, 21]
lbrow = [22, 23, 24, 25, 26]
reye = [36, 37, 38, 39, 40, 41]
leye = [42, 43, 44, 45, 46, 47]

bblip = [55, 56, 57, 58, 59]
ttlip = [49, 50, 51, 52, 53]

tblip = [65, 66, 67]
btlip = [61, 62, 63]
nose_bridge = [27, 28, 29, 30]
nose = [31, 32, 33, 34, 35]

rbrow_dist = [41, 19]
lbrow_dist = [46, 24]

reye_width = [36, 39]
leye_width = [42, 45]
reye_dist = [37, 41]
leye_dist = [44, 46]
lnose_dist = [30, 14]
rnose_dist = [30, 2]
mouth_dist = [51, 57]
nose_dist = [27, 30]

nose_tip = 30
nose_tip_avg = (0, 0)
count = 0
x = 0
y = 0
shape = None
frame = None

RED = (255, 0, 0)
BLUE = (0, 0, 255)


class VidApp(QWidget):

    def __init__(self, *args, **kwargs):
        super(VidApp, self).__init__(*args, **kwargs)
        self.frame = None
        self.liveControl = False
        self.record = False
        self.startTime = 0
        self.liveTime = 0
        self.video_size = QSize(640,480)
        self.shape = None
        self.predictor = None
        self.detector = None
        self.setup_ui()
        self.setup_camera()
        self.rmin = 999
        self.rmax = -999
        self.lmin = 999
        self.lmax = -999
        self.init_cv()

    def init_cv(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(
            os.path.join(os.path.dirname(__file__), "shape_predictor_68_face_landmarks.dat"))

        self.kalman = cv2.KalmanFilter(2, 1, 0)
        self.state = 0.1 * np.random.randn(2, 1)
        self.kalman.transitionMatrix = np.array([[1., 1.], [0., 1.]])
        self.kalman.measurementMatrix = 1. * np.ones((1, 2))
        self.kalman.processNoiseCov = 1e-5 * np.eye(2)
        self.kalman.measurementNoiseCov = 1e-1 * np.ones((1, 1))
        self.kalman.errorCovPost = 1. * np.ones((2, 2))
        self.kalman.statePost = 0.1 * np.random.randn(2, 1)

    #    def calc_point(self,angle):
    #       return (np.around(self.video_size.width() / 2 + self.video_size.width()/ 3 * cos(angle), 0).astype(int),
    #               np.around(self.video_size.height() / 2 - self.video_size.width() / 3 * sin(angle), 1).astype(int))

    def _toggle_rgb(self):
        pass

    def plot_point(self, pt, color=(255, 255, 255)):
        x, y = pt
        cv2.circle(self.frame, (x, y), 1, color, -1)

    def kalman_loop(self, pt):
        self.state = pt
        # state_angle = self.state[pt[0], pt[1]]
        # state_pt = self.calc_point(state_angle)
        prediction = self.kalman.predict()
        # predict_angle = prediction[0, 0]
        # predict_pt = self.calc_point(predict_angle)
        measurement = self.kalman.measurementNoiseCov * np.random.randn(1, 1)
        # generate measurement
        measurement = np.dot(self.kalman.measurementMatrix, self.state) + measurement
        # measurement_angle = measurement[0, 0]
        # measurement_pt = self.calc_point(measurement_angle)

        self.plot_point(self.state, color=RED)
        # self.plot_point(predict_pt, color=BLUE)
        # self.plot_point(measurement_pt, color=QColor.cyan())

        self.kalman.correct(measurement)
        process_noise = sqrt(self.kalman.processNoiseCov[0, 0]) * np.random.randn(2, 1)
        self.state = np.dot(self.kalman.transitionMatrix, self.state) + process_noise

    def setup_ui(self):
        """Initialize widgets.
        """
        self.image_label = QLabel()
        self.image_label.setFixedSize(QSize(640,480))

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)

        self.calibrate = QPushButton('live')
        self.calibrate.clicked.connect(self._toggleLive)

        self.recordButton = QPushButton('record')
        self.recordButton.clicked.connect(self._toggleRecord)

        self.dumpButton = QPushButton('record')
        self.dumpButton.clicked.connect(self._dump)

        self.toggleColor = QPushButton('toggle rgb')
        self.toggleColor.clicked.connect(self._toggle_rgb)

        self.xlabel = QLabel("0.0")
        self.ylabel = QLabel("0.0")
        ho = QHBoxLayout()
        ho.addWidget(self.calibrate)
        ho.addWidget(self.recordButton)
        #ho.addWidget(self.toggleColor)
        ho.addWidget(self.xlabel)
        ho.addWidget(self.ylabel)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.image_label)
        self.main_layout.addLayout(ho)
        self.main_layout.addWidget(self.quit_button)
        self.setLayout(self.main_layout)

    def setup_camera(self):
        """Initialize camera.
        """
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_size.width())
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_size.height())
        self.timer = QTimer()
        self.timer.timeout.connect(self.the_loop)
        self.timer.start(30)

    def display_video_stream(self):
        _, self.frame = self.capture.read()
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        self.frame = cv2.flip(self.frame, 1)
        image = QImage(self.frame, self.frame.shape[1], self.frame.shape[0],
                       self.frame.strides[0], QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(image))

    def _toggleRecord(self):
        self.record = not self.record
        if self.record:
            self.startTime = time.time()
            self.liveTime = time.time() - self.startTime

    def _toggleLive(self):
        self.liveControl = not self.liveControl

    def plot_feature(self, feature, color=(0, 0, 255)):
        if feature is None:
            return
        p1 = (self.shape[feature[0]][0], self.shape[feature[0]][1])
        p2 = (self.shape[feature[1]][0], self.shape[feature[1]][1])
        cv2.line(self.frame, p1, p2, color)
        dx = abs(self.shape[feature[0]][0] - self.shape[feature[1]][0])
        dy = abs(self.shape[feature[0]][1] - self.shape[feature[1]][1])
        d = math.sqrt(dx * dx + dy * dy)
        return d

    def _dump(self):
        pass

    def the_loop(self):
        rnorm = 1
        lnorm = 1
        _, self.frame = self.capture.read()
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        self.frame = cv2.flip(self.frame, 1)
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        # detect faces in the grayscale self.frame
        rects = self.detector(gray, 0)

        self.frame = np.zeros((480, 640, 3), np.uint8)
        # loop over the face detections
        for rect in rects:
            self.shape = self.predictor(gray, rect)
            self.shape = face_utils.shape_to_np(self.shape)
            if self.shape is not None:
                for i, (x, y) in enumerate(self.shape):
                    # hacky way to color each section (left eyebrow, bottom lip, etc)
                    color = (255, 255, 255)
                    '''
                    if i in rbrow or i in bblip:
                        color = (0, 255, 0)
                    elif i in lbrow or i in btlip:
                        color = (0, 0, 255)
                    elif i in reye or i in ttlip:
                        color = (255, 0, 255)
                    elif i in leye or i in tblip or i in nose:
                        color = (0, 255, 255)
                    '''
                    cv2.circle(self.frame, (x, y), 1, color, -1)

                # The following code attempts to get a normalized eye-openness value
                # distance between sides of eyes
                w1 = self.plot_feature(reye_width, color=(0, 0, 0))
                w2 = self.plot_feature(leye_width, color=(0, 0, 0))
                # distance (height) of top to bottom eyelid
                d1 = self.plot_feature(reye_dist, color=(255, 0, 0))
                d2 = self.plot_feature(leye_dist, color=(0, 0, 255))
                # ratio of height to width
                rr = d1 / w1
                lr = d2 / w2
                # record min/max
                if rr > self.rmax:
                    self.rmax = rr
                if rr < self.rmin:
                    self.rmin = rr
                if lr > self.lmax:
                    self.lmax = lr
                if lr < self.lmin:
                    self.lmin = lr
                # normalize current position against historical min/max
                # rnorm = abs(self.rmax-self.rmin)   /abs(rr-self.rmin)
                # lnorm = abs(self.lmax - self.lmin) / abs(lr - self.lmin)

                try:
                    rnorm = abs(rr - self.rmin) / abs(self.rmax - self.rmin)
                    lnorm = abs(lr - self.lmin) / abs(self.lmax - self.lmin)
                except ZeroDivisionError:
                    pass

                # clamp to 0,1
                rnorm = max(min(rnorm, 1), 0)
                lnorm = max(min(lnorm, 1), 0)
                self.xlabel.setText('{0:.4f} - {1:.4f}'.format(rnorm, lnorm))

                d1 = self.plot_feature(rbrow_dist, color=(10, 100, 100))
                d2 = self.plot_feature(lbrow_dist, color=(122, 99, 123))
                self.plot_feature(nose_dist, color=(0, 0, 0))
                self.plot_feature(mouth_dist, color=(123, 231, 0))
                n1 = self.plot_feature(lnose_dist, color=(235, 0, 0))
                n2 = self.plot_feature(rnose_dist)
                # self.xlabel.setText('{0:.2f},{1:.2f}'.format(n1, n2))

                # avg cheek height
                ach = (self.shape[rnose_dist[1]][1] + self.shape[lnose_dist[1]][1]) / 2.0
                yv = self.shape[nose_tip][1] - ach
                yv *= -0.02
                # self.xlabel.setText('{0:.4f}'.format(yv))

                self.kalman_loop(self.shape[reye_dist[0]])

                xt = n1 / (n1 + n2)
                self.ylabel.setText('{0:.4f}'.format(xt))
                if self.liveControl:
                    self.liveTime = time.time() - self.startTime
                    xv = -(xt - 0.5)
                    cmds.xform('x:mech_eyes_all_ctrl', t=(xv, yv, 0))
                    cmds.xform('x:mech_eye_R_ctrl', s=(1, rnorm + 0.01, 1))
                    cmds.xform('x:mech_eye_L_ctrl', s=(1, lnorm + 0.01, 1))
                    if self.record:
                        cmds.setKeyframe('x:mech_eye_R_ctrl', t=self.liveTime)
                        cmds.setKeyframe('x:mech_eye_L_ctrl', t=self.liveTime)
                        cmds.setKeyframe('x:mech_eyes_all_ctrl', t=self.liveTime)
        #  key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        # if key == ord("q"):
        #    self.close()

        image = QImage(self.frame, self.frame.shape[1], self.frame.shape[0],
                       self.frame.strides[0], QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(image))

    def close(self, *args, **kwargs):
        self.timer.stop()
        # do a bit of cleanup
        cv2.destroyAllWindows()
        self.capture.release()
        global dockControl

        try:
            cmds.deleteUI("vid")
        except:
            print "deleteUI vid didnt work"
        try:
            self.destroy()
        except:
            print "destroy didnt work"

        try:
            cmds.deleteUI(dockControl)
        except:
            print "couldnt delete control"

        try:
            super(VidApp, self).close()
        except:
            print "not super"


ui = None
dockWidget = None
dockControl = None


def main():
    global dockControl
    # app = QApplication(sys.argv)
    # win = MainApp()
    # win.show()
    # sys.exit(app.exec_())
    ui, dockWidget, dockControl = Dock(VidApp, width=320, winTitle='vid')


if __name__ == "__main__":
    main()
