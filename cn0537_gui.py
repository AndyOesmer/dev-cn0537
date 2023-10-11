from gui55 import Ui_MainWindow
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QSlider, QLabel
)
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget
from time import sleep
import random
from threading import Thread
import serial
import sys

class CN0537:
    def __init__(self, port, baudrate):
        self.port = port #
        self.baudrate = baudrate #
        self.parity = 'N'
        self.stopbits = serial.STOPBITS_ONE
        self.xonxoff = True
        self.rtscts = True
        self.timeout = 1
        self.bytesize = 8
        self.data_blue = 0
        self.data_ir = 0
        self.data_temp = 0
        self.data_humid = 0
        
        try: 
            self.ser = serial.Serial(
                port= self.port,
                baudrate = self.baudrate,
                parity = self.parity,
                stopbits = self.stopbits,
                xonxoff = self.xonxoff,
                rtscts = self.rtscts,
                timeout = self.timeout,
                bytesize = self.bytesize)
            #self.ser.open()
        except Exception as e:
            print(e)
            print("Serial error")
        

    def Start(self):
        
        sleep(3)
        self.ser.write(b"os 2\r\n")
        sleep(0.1)
        self.ser.write(b"s\r\n")
        sleep(1)
        print("Device ok!")
        print("Device open!")
        sleep(3)
        print("Waiting bits:")
        print(self.ser.in_waiting)
    
    def Stop(self):
        # self.ser.write(b"i \r\n") # STOP STREAM
        # sleep(0.1)
        print("STOP")
    
    def Reset(self): # NOT USED
        self.ser.write(b"ar\r\n")
        sleep(0.1)
        print("Redo initialization")

    def StopAlarm(self):
        self.ser.write(b"ra\r\n")
        sleep(1)
        
        print("Alarm Stopped!")

        self.ser.write(b"i \r\n")
        sleep(0.1)
        print("STOP. ALARM TRIGGERED")
    
    def readSerial(self): 

        if self.ser.in_waiting > 0:
            serialString = self.ser.readline()
            try:
                line = serialString.decode("Ascii")
                print(line)
                
                data = line.strip('\t').split(' ')
                blue = float(data[0])
                ir = float(data[1])
                status = float(data[3])
                temp = float(data[5])
                humid = float(data[6])

                self.data_blue = blue
                self.data_ir = ir
                self.data_temp = temp
                self.data_humid = humid
                print(blue)
                return blue, ir, temp, humid, status
            except Exception as e:
                return 0,0,0,0,0
        else:
            print("hello")
            return self.data_blue, self.data_ir, self.data_temp, self.data_humid, 0

# BULB_HEIGHT = 300
# BULB_WIDTH = 150

class CN0537_GUI(QMainWindow):
    def __init__(self):
        
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle("CN0537 - Smart Smoke Detection System")
        self.window()
        self.button_action()
        self._createBulb()


        self.thread = DataReader()
        self.thread.output[float, float, float, float, int, int].connect(self.updateAll)


    def window(self):
        
        # Blue Plot
        self.Blueplot_widget = LivePlotWidget()
        self.Blueplot_curve = LiveLinePlot()
        self.Blueplot_widget.addItem(self.Blueplot_curve)
        self.ui.verticalLayout_19.addWidget(self.Blueplot_widget)
        # DataConnector holding 600 points and plots @ 100Hz
        self.Bluedata_connector = DataConnector(self.Blueplot_curve, max_points=600, update_rate=100)
      
        # # IR Plot
        self.IR_widget = LivePlotWidget()
        self.IR_curve = LiveLinePlot()
        self.IR_widget.addItem(self.IR_curve)
        self.ui.verticalLayout_20.addWidget(self.IR_widget)
        # DataConnector holding 600 points and plots @ 100Hz
        self.IRdata_connector = DataConnector(self.IR_curve, max_points=600, update_rate=100)
        
        # Temp Data
        #self.templayout = QVBoxLayout(self.ui.temp)
        self.temp_value = QLineEdit()
        self.temp_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_value.setReadOnly(True)
        self.ui.verticalLayout_16.addWidget(self.temp_value)

        # Hum Data
        #self.humlayout = QVBoxLayout(self.ui.hum)
        self.hum_value = QLineEdit()
        self.hum_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hum_value.setReadOnly(True)
        self.ui.verticalLayout_17.addWidget(self.hum_value)

    def button_action(self):
        self.blueplot_setup()
        self.ui.stopbutton.clicked.connect(self.Stop)
        self.ui.resetbutton.clicked.connect(self.clear)
        self.ui.stopalarmbutton.clicked.connect(self.AlarmStop)
        self.ui.resetbutton.clicked.connect(self.AlarmStop)


    def blueplot_setup(self):
        self.ui.startbutton.clicked.connect(self.startReader)


    def startReader(self):
        self.thread.startdev()
        self.thread.start()

    def Stop(self):
        self.thread.stop()
        self.thread.exit()
        print("screen")
    def AlarmStop(self):
       self.thread.stopAlarm()

    def clear(self):
        self.Blueplot_widget.clear()
        self.IR_widget.clear()
        # self.device.ser.write(b"ra\r\n")
        self.running = False
        sleep(0.1)

        self.Blueplot_curve = LiveLinePlot()
        self.Blueplot_widget.addItem(self.Blueplot_curve)
        # DataConnector holding 600 points and plots @ 100Hz
        self.Bluedata_connector = DataConnector(self.Blueplot_curve, max_points=600, update_rate=100)

        self.IR_curve = LiveLinePlot()
        self.IR_widget.addItem(self.IR_curve)
        # DataConnector holding 600 points and plots @ 100Hz
        self.IRdata_connector = DataConnector(self.IR_curve, max_points=600, update_rate=100)

        self.thread.reset()

    def _createBulb(self):
        #self.bulblayout = QVBoxLayout(self.ui.alarmframe)
        
        temp = False

        self.bulb = QLabel()
        if(temp==True):
            self.bulb.setStyleSheet("QLabel"
                            "{"
                            "background-color : red;"
                            "}")
        else:
            self.bulb.setStyleSheet("QLabel"
                    "{"
                    "background-color : green;"
                    "}")
        
        #self.bulblayout.addWidget(self.bulb)
        #self.bulb.setFixedSize(BULB_WIDTH, BULB_WIDTH)
        self.ui.verticalLayout_14.addWidget(self.bulb)
   

    def updateAll(self, a, b, c, d, e, x):
        blue = a
        ir = b
        Blue = self.Bluedata_connector
        Ir = self.IRdata_connector
        td = self.temp_value
        hd = self.hum_value
        bulb = self.bulb
        # Callback to plot new data point

        Blue.cb_append_data_point(blue, x)
        Ir.cb_append_data_point(ir, x)
        td.setText(str(c)+'°C')
        font = td.font()      # lineedit current font
        font.setPointSize(60)
        #font.setAlignment(Qt.AlignmentFlag.AlignCenter)               # change it's size
        td.setFont(font)
        
        hd.setText(str(d)+'%')
        font = hd.font()      # lineedit current font
        font.setPointSize(60)  
        #font.setAlignment(Qt.AlignmentFlag.AlignCenter)            # change it's size
        hd.setFont(font)
        print(e)

        if e == 1:
            bulb.setStyleSheet("QLabel"
                "{"
                    "background-color : red;"
                    "}")
        elif e == 0:
            bulb.setStyleSheet("QLabel"
                    "{"
                    "background-color : green;"
                    "}")



class DataReader(QThread):
    output = Signal(float,float,float,float,int,int)

    def __init__(self):
        QThread.__init__(self, parent = None)
        self.device = CN0537('COM4',115200)
        self.running = False

    def run(self):
        """Sine wave generator"""
        self.x = 0
        # self.Blueplot_widget.clear()
        #print("1" + str(self.running))
        while True:
            if self.running:
                a, b, c, d, e = self.device.readSerial()
                self.x += 1
                self.output.emit(a, b, c ,d ,e, self.x)
                sleep(0.1)
    
    def stop(self):
        self.running = False
        self.device.Stop()
        self.x = 0

    def stopAlarm(self):
        self.device.StopAlarm()
        self.stop()
        self.x = 0

    def startdev(self):
        self.running = True
        self.device.Start()
        sleep(0.1)

    def reset(self):
        self.device.ser.flush()
        self.x = 0

    def __del__(self):    
        self.wait()
    
    
        
def main():
    app = QApplication([])
    #dev = CN0537('COM4',115200)
    cn0537_gui = CN0537_GUI()
    cn0537_gui.show()
    sys.exit(app.exec())
        

if __name__ == "__main__":
    main()