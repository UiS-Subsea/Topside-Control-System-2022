import multiprocessing
from tkinter import Widget
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QFileDialog, QApplication, QWidget, QVBoxLayout, QSizeGrip, QFrame, QMessageBox, QStyleFactory, QSizeGrip, QGraphicsDropShadowEffect, QPushButton, QComboBox, QDesktopWidget
from PyQt5.QtWebEngineWidgets import *
from PyQt5.Qt import *
from PyQt5.QtGui import QColor, QIcon, QCursor
from multiprocessing import Pipe, Value
from Threadwatch import Threadwatcher
import sys
import threading
import json
import os
import Subsea_QT_GUI.SUBSEAGUI as SUBSEAGUI
from Subsea_QT_GUI.custom_grips import CustomGrip, Widgets
from PyQt5.QtCore import Qt, QtMsgType, QTimer, QEvent


# GLOBALS
# ///////////////////////////////////////////////////////////////
GLOBAL_STATE = False
GLOBAL_TITLE_BAR = True

# os.system('pyuic5 -x NYGUI.ui -o SUBSEAGUI.py')
os.environ["QT_FONT_DPI"] = "96" # FIX Problem for High DPI and Scale above 100%

class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self, port):
        super().__init__()
        layout = QHBoxLayout()
        self.label = QLabel("Another Window")

        self.setWindowTitle(f"{'havbunnskamera' if port-6888 == 0 else 'frontkamera'}")
        self.setWindowIcon(QtGui.QIcon('Subsea_QT_GUI/images/camera.png'))

        self.url = f"http://10.0.0.2:{port}/cam.html"
        self.stream1 = QWebEngineView(self)
        self.stream1.setFixedWidth(1920)
        self.stream1.setFixedHeight(1080)
        self.stream1.load(QtCore.QUrl(self.url))
        self.setLayout(layout)

        if len(QtWidgets.QApplication.screens())>2:
            monitor = QDesktopWidget().screenGeometry(int(f"{port-6887}"))
            self.move(monitor.left(), monitor.top())
            self.showFullScreen()
        else:
            self.showMaximized()

PROFILE_UPDATE_ID = 2
COMMAND_TO_ROV_ID = 3

class Window(QMainWindow, SUBSEAGUI.Ui_MainWindow):
    def __init__(self, pipe_conn_only_rcv, queue: multiprocessing.Queue, t_watch: Threadwatcher, id: int, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QtGui.QIcon('Subsea_QT_GUI/images/logo.png'))
        self.queue = queue
        self.pipe_conn_only_rcv = pipe_conn_only_rcv
        self.t_watch = t_watch
        self.id = id



        
        # Remove frame around window
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setup_gui_with_folder_change()

        # Menu button clicked
        self.kontroller_btn.clicked.connect(lambda: self.change_current_widget(2))
        self.informasjon_btn.clicked.connect(lambda: self.change_current_widget(1))

        # "Lag ny profil"-button clicked
        self.make_new_profile_btn.clicked.connect(self.browse_files)
        #self.make_new_profile_btn.clicked.connect(self.make_new_profile)

        # "Reset"-button clicked
        self.reset_btn.clicked.connect(self.reset_profile)

        # "Lagre"-button clicked
        self.save_profile_btn.clicked.connect(self.save_profile)

        # GUI button clicked
        self.manuell_btn.clicked.connect(self.button_test)

        self.init_drop_shadow()



        # ///////////////////////////////////////////////////////////////
        self.titleRightInfo.mouseDoubleClickEvent = self.dobleClickMaximizeRestore
        #self.maximizeRestoreAppBtn.mouseDoubleClickEvent = self.dobleClickMaximizeRestore

        self.titleRightInfo.mouseMoveEvent = self.moveWindow

        # STANDARD TITLE BAR
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)


        # CUSTOM GRIPS
        self.left_grip = CustomGrip(self, Qt.LeftEdge, True)
        self.right_grip = CustomGrip(self, Qt.RightEdge, True)
        self.top_grip = CustomGrip(self, Qt.TopEdge, True)
        self.bottom_grip = CustomGrip(self, Qt.BottomEdge, True)

        # RESIZE WINDOW
        self.sizegrip = QSizeGrip(self.frame_size_grip)
        self.sizegrip.setStyleSheet("width: 20px; height: 20px; margin 0px; padding: 0px;")

        # MINIMIZE
        self.minimizeAppBtn.clicked.connect(self.minimize)
        
        # MAXIMIZE/RESTORE
        self.maximizeRestoreAppBtn.clicked.connect(self.maximize_restore)

        # CLOSE APPLICATION
        self.closeAppBtn.clicked.connect(self.shutdown)
        # ///////////////////////////////////////////////////////////////

        self.connect_test_values()
        #self.start_camera_windows()

        self.recieve = threading.Thread(target=self.recieve_and_set_text, daemon=True, args=(self.pipe_conn_only_rcv,))
        self.recieve.start()
        # print(f"type of self.widget: {type(self.widget)}")

        self.btn_combobox_list:list[QComboBox] = [self.comboBox_A_btn, self.comboBox_B_btn, self.comboBox_X_btn, self.comboBox_Y_btn, self.comboBox_RB_btn, self.comboBox_LB_btn, self.comboBox_left_stick_btn, self.comboBox_right_stick_btn, self.comboBox_view_btn, self.comboBox_menu_btn]
        btn_command_list:list[str] = []
        with open("button_config.txt") as btn_config:
            btn_command_list = [line.strip() for line in btn_config.readlines()]
        for btn in self.btn_combobox_list:
            btn.addItems(btn_command_list)
            btn.currentIndexChanged.connect(self.send_profile_to_main)

        self.setStyle(QStyleFactory.create('Windows'))
        self.comboBox_Y_btn.setStyle(QStyleFactory.create('Windows'))
    
    def set_default_profile(self):
        pass

    def send_command_to_rov(self, command):
        self.send_data_to_main(command, COMMAND_TO_ROV_ID)

    def send_profile_to_main(self):
        self.send_data_to_main([btn.currentIndex() for btn in self.btn_combobox_list], PROFILE_UPDATE_ID)
    

    def make_new_profile(self):
        # Trykker på "Lag ny profil"
        # Skal oppgi navn på profilen og lagre en fil med det som er valgt i comboboxen
        pass

    def reset_profile(self):
        # Trykker på "Reset"
        # Skal endre combobox-valgene til standard profil
        # Må ha en 'standard_profil.txt' som skal lastes inn
        pass

    def save_profile(self):
        # Det er allerede laget en fil.
        # (ellers kan det komme opp: "Du har ikke gjort noen endring")
        # Skal lagre endringene gjort i comboboxen til denne filen når man trykker på "Lagre"
        pass

    def browse_files(self):
        # RESET-KNAPP
        # Skal laste inn ny profil når man velger en egendefinert profil i comboboxen
        #fname = QFileDialog.getSaveFileName(self, 'Save file', 'Custom-profile')
        #if len(fname[0]):
        #    print(fname[0])
            #self.filename.setText(fname) # for å vise fram filepath
        msg = QMessageBox()
        msg.setWindowTitle("Melding")
        msg.setText("Profilen er satt til standard")
        msg.setIcon(QMessageBox.Warning)
        x = msg.exec_()



        

        

        
    def send_data_to_main(self, data, id):
        if self.queue is not None:
            self.queue.put(id, data)

    def shutdown(self):
        self.t_watch.stop_all_threads()
        #for window in self.child_window:
        #    window.close()
        self.close()
        exit(0)

    def button_works(self):
        print("function activated")

    def start_camera_windows(self):
        self.child_window: list[AnotherWindow] = []

        self.child_window.append(AnotherWindow(6888))
        self.child_window[0].show()

        self.child_window.append(AnotherWindow(6889))
        self.child_window[1].show()


    def setup_gui_with_folder_change(self):
        os.chdir("Subsea_QT_GUI")
        self.setupUi(self)
        os.chdir("..")

    def update_gui(self, data):
        if self.t_watch.should_run(self.id):
            self.dybde.setText(str(round(data["dybde"],4)))
            self.tid.setText(str(data["tid"]))
            self.spenning.setText(str(round(data["spenning"],4)))
            self.temp_vann.setText(str(round(data["temp_vann"],4)))

    def recieve_and_set_text(self, conn):
        while self.t_watch.should_run(self.id):
            # print("trying to take out of pipe")
            sensordata = conn.recv()
            # print(sensordata)
            self.update_gui(sensordata)
        print("recieved close thread. trying to close")
        self.shutdown()
        exit(0)
        
    def button_test(self):
        # print("Clicked on button")
        self.w1.stream1.load(QtCore.QUrl("http://vg.no"))
        self.w2.stream1.load(QtCore.QUrl("http://vg.no"))

    def change_current_widget(self, index):
        print(f"should change to widget {index}")
        self.stackedWidget.setCurrentIndex(index)

    # ///////////////////////////////////////////////////////////////
    def init_drop_shadow(self):
        # DROP SHADOW
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(17)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.bgApp.setGraphicsEffect(self.shadow)

        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowMinimizeButtonHint|Qt.WindowCloseButtonHint)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.appMargins.setContentsMargins(10, 10, 10, 10)

    ## SET VALUES TO DEF progressBarValue
    def setValue(self, slider, labelPercentage, progressBarName, color):
        # GET SLIDER VALUE
        value = slider.value()
        # CONVERT VALUE TO INT
        sliderValue = int(value)
        # HTML TEXT PERCENTAGE
        htmlText = """<p align="center"><span style=" font-size:9pt;">{VALUE}</span><span style=" font-size:9pt; vertical-align:super;">%</span></p>"""
        labelPercentage.setText(htmlText.replace("{VALUE}", str(sliderValue)))
        # CALL DEF progressBarValue
        self.progressBarValue(sliderValue, progressBarName, color)


    ## DEF PROGRESS BAR VALUE
    def progressBarValue(self, value, widget, color):
        # GET PROGRESS BAR VALUE, CONVERT TO FLOAT AND INVERT VALUES
        # stop works of 1.000 to 0.000
        progress = (100 - value) / 100.0
        if value >= 0:
            # PROGRESSBAR STYLESHEET BASE
            styleSheet = """ QFrame{ border-radius: 30px;background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(255, 0, 127, 0), stop:{STOP_2} {COLOR}); }"""
            # GET NEW VALUES
            stop_1 = str(progress - 0.001)
            stop_2 = str(progress)
        else:
            # PROGRESSBAR STYLESHEET BASE
            styleSheet = """QFrame{ border-radius: 30px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(255, 0, 127, 0), stop:{STOP_2} rgb(226, 47, 53)); }"""
            # GET NEW VALUES
            stop_1 = str(progress - 1)
            stop_2 = str(progress - 0.001 -1)

        # FIX MAX VALUE
        if value == 100:
            stop_1 = "1.000"
            stop_2 = "1.000"

        # SET VALUES TO NEW STYLESHEET
        newStylesheet = styleSheet.replace("{STOP_1}", stop_1).replace("{STOP_2}", stop_2).replace("{COLOR}", color)

        # APPLY STYLESHEET WITH NEW VALUES
        widget.setStyleSheet(newStylesheet)

    def connect_test_values(self):
        # APPLY VALUES TO PROGREESBAR
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.VHF_percentage, self.VHF, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.HVF_percentage, self.HVF, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.VVF_percentage, self.VVF, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.HHF_percentage, self.HHF, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.HVF_percentage, self.HVF, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.VVB_percentage, self.VVB, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.HVB_percentage, self.HVB, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.HVB_percentage, self.HVB, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.VHB_percentage, self.VHB, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.HHB_percentage, self.HHB, "rgba(85, 170, 255, 255)"))

        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.mani_percentage_1, self.mani_1, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.mani_percentage_2, self.mani_2, "rgba(85, 170, 255, 255)"))
        self.slider.valueChanged.connect(lambda: self.setValue(self.slider, self.mani_percentage_3, self.mani_3, "rgba(85, 170, 255, 255)"))

        self.lys_slider.valueChanged.connect(lambda: self.setValue(self.lys_slider, self.lys_percentage, self.lys, "rgba(85, 170, 255, 255)"))

    # MOUSE CLICK EVENTS
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

    def resizeEvent(self, event):
        # Update Size Grips
        self.resize_grips()

    def minimize(self):
        print("clicked minimized")
        if sys.platform == "darwin" or sys.platform.startswith("linux"):
            self.hide()
        elif sys.platform == "win32":
            self.showMinimized()
        


    def maximize_restore(self):
        global GLOBAL_STATE
        status = GLOBAL_STATE
        if status == False:
            if sys.platform == "darwin" or sys.platform.startswith("linux"):
                self.showFullScreen()
            elif sys.platform == "win32":
                self.showMaximized()
            GLOBAL_STATE = True
            self.appMargins.setContentsMargins(0, 0, 0, 0)
            self.maximizeRestoreAppBtn.setToolTip("Restore")
            self.maximizeRestoreAppBtn.setIcon(QIcon(u":/icons/images/icons/icon_restore.png"))
            self.frame_size_grip.hide()
            self.left_grip.hide()
            self.right_grip.hide()
            self.top_grip.hide()
            self.bottom_grip.hide()
        else:
            GLOBAL_STATE = False
            self.showNormal()
            self.resize(self.width()+1, self.height()+1)
            self.appMargins.setContentsMargins(0, 0, 0, 0)
            self.maximizeRestoreAppBtn.setToolTip("Maximize")
            self.maximizeRestoreAppBtn.setIcon(QIcon(u":/icons/images/icons/icon_maximize.png"))
            self.frame_size_grip.show()
            self.left_grip.show()
            self.right_grip.show()
            self.top_grip.show()
            self.bottom_grip.show()


    def dobleClickMaximizeRestore(self, event):
        # IF DOUBLE CLICK CHANGE STATUS
        if event.type() == QEvent.MouseButtonDblClick:
            QTimer.singleShot(250, lambda: self.maximize_restore())

    def moveWindow(self, event):
        # IF MAXIMIZED CHANGE TO NORMAL
        if self.returnStatus():
            self.maximize_restore()
        # MOVE WINDOW
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def resize_grips(self):
            ENABLE_CUSTOM_TITLE_BAR = True
            self.left_grip.setGeometry(0, 10, 10, self.height())
            self.right_grip.setGeometry(self.width() - 10, 10, 10, self.height())
            self.top_grip.setGeometry(0, 0, self.width(), 10)
            self.bottom_grip.setGeometry(0, self.height() - 10, self.width(), 10)

    # RETURN STATUS
    def returnStatus(self):
        return GLOBAL_STATE

    # SET STATUS
    def setStatus(self, status):
        global GLOBAL_STATE
        GLOBAL_STATE = status
    # ///////////////////////////////////////////////////////////////



def run(conn, queue_for_rov, t_watch: Threadwatcher, id):
    app = QtWidgets.QApplication(sys.argv)

    
    win = Window(conn, queue_for_rov, t_watch, id)
    win.setWindowTitle("UiS Subsea")
    GLOBAL_STATE = False

    win.maximize_restore() # for windows
    #win.showFullScreen() # for mac
    #win.showMinimized()
    win.show()
    # win.close()
    sys.exit(app.exec())
  

if __name__ == "__main__":
    import SUBSEAGUI

    
    run()
