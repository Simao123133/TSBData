from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget
import pyqtgraph as pg
from ReadData import time_value_pair
import numpy as np
import numexpr as ne
import datetime
import threading
import paho.mqtt.client as mqtt
import json
import random
import time
import sys
from ReadData import get_data
import signal
from qdarkstyle import load_stylesheet

def signal_handler(sig, frame):

    global client, thread_exit
    print('You pressed Ctrl+C!')
    if (Real_time == 1):
        client.loop_stop()
        client.disconnect()
        thread_exit = 1
    sys.exit(0)

class plot_obj(object):
    def __init__(self):
        
        self.plot = []
        self.plot_index = []
        self.used_colors = []
        self.plot_color = []
        self.names = []
        self.plotted = []

        for j in range(100):
            self.used_colors.append(0)

        self.date_axis = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.graphicsView = PlotWidget(ui.centralwidget, axisItems = {'bottom': self.date_axis})   
        self.comboBox = QtWidgets.QComboBox(ui.centralwidget)
        self.comboBox.activated.connect(self.draw)
        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.hline = pg.InfiniteLine(angle=0, movable=False)
        self.graphicsView.addItem(self.vline, ignoreBounds=True)
        self.graphicsView.addItem(self.hline, ignoreBounds=True)
        self.curve = self.graphicsView.plot(x=[], y=[])
        self.curve.scene().sigMouseMoved.connect(self.mouseMoved)
        self.curve.scene().sigMouseClicked.connect(self.mouseClicked)
        self.graphicsView.addLegend(offset=(0.1, 0.1))
        self.autoscale = QtWidgets.QPushButton(ui.centralwidget)
        self.autoscale.setText('Auto Scale')
        self.autoscale.clicked.connect(self.AutoScale)
        self.clear = QtWidgets.QPushButton(ui.centralwidget)
        self.clear.setText('Clear')
        self.clear.clicked.connect(self.funcToClear)

    def mouseClicked(self,event):

        ui.follow = 0

    def init_variables(self):
        self.plot = []
        self.plot_index = []
        self.used_colors = []
        self.plot_color = []
        self.names = []
        self.plotted = []

        for j in range(100):
            self.used_colors.append(0)

    def draw(self):

        index = self.names.index(self.comboBox.currentText())
        color_index = self.min_index(self.used_colors)
        color = ui.colors[color_index]

        if(self.plotted[index] == 0):
            
            self.plot_color.append(color_index)
            legend = names_or[index][len(str(index))+2:]+ "  [" + dataset.signal[index].unit+"]"
            self.plot.append(self.graphicsView.plot(dataset.signal[index].time, dataset.signal[index].value, pen=color, name=legend)) 
            self.plot_index.append(index)
            self.comboBox.setItemText(index, self.names[index]+" plotted --------------------")
            self.names[index] = self.names[index]+" plotted --------------------"
            self.plotted[index] = 1    
            self.used_colors[color_index] = 1

            if len(self.plot) == 1:
                self.AutoScale()

        else:
            self.graphicsView.removeItem(self.plot[self.plot_index.index(index)])
            self.used_colors[self.plot_color[self.plot_index.index(index)]] = 0
            self.plot_color.pop(self.plot_index.index(index))
            self.plot.pop(self.plot_index.index(index))
            self.plot_index.remove(index)
            self.plotted[index] = 0
            self.names[index] = names_or[index]
            self.comboBox.setItemText(index, self.names[index])

    def mouseMoved(self,point):
        p = self.graphicsView.plotItem.vb.mapSceneToView(point)

        x = float("{0:.3f}".format(p.x()))
        y = float("{0:.3f}".format(p.y()))
        x_time = str(datetime.timedelta(seconds=x))[0:10]
        if time.time() - ui.statusbar_timer > 3:
            ui.label.setText(f"P: {x_time, y}" + "={} [s]".format(x))
        self.vline.setPos(p.x())
        self.hline.setPos(p.y())

    def AutoScale(self):
        self.graphicsView.enableAutoRange(axis='y')
        self.graphicsView.setAutoVisible(y=True)

    def funcToClear(self):
        for index in self.plot_index:
            self.comboBox.setItemText(index, names_or[index])
            self.plotted[index] = 0
            self.graphicsView.removeItem(self.plot[self.plot_index.index(index)])
            self.names[index] = names_or[index]
            self.used_colors[self.plot_color[self.plot_index.index(index)]] = 0
        
        self.plot_color.clear()
        self.plot.clear()
        self.plot_index.clear()

    def update(self):

        for j in range(len(self.plot)):
            if len(dataset.signal[self.plot_index[j]].time) == len(dataset.signal[self.plot_index[j]].value):           
                self.plot[j].setData(dataset.signal[self.plot_index[j]].time,dataset.signal[self.plot_index[j]].value)  
        if ui.follow == 1 and len(self.plot) > 0:        
            self.graphicsView.setXRange(time.time()-start_time-ui.time_window, time.time()-start_time) 

    def min_index(self, list):

            for i in range(len(list)):
                if list[i] == 0:
                    return i 

class dataset_obj(object):
    def __init__(self):

        self.signal = []   

class new_signal(object):
    def __init__(self, exp, time_index, new_index):

        self.exp = exp
        self.time_index = time_index
        self.new_index = new_index

    def update(self):
        
        if dataset.signal[self.time_index].time[-1] != dataset.signal[self.new_index].time[-1]:
            value = ne.evaluate(self.exp, global_dict = ui.translation_last)
            dataset.signal[self.new_index].update(dataset.signal[self.time_index].time[-1], value)
            ui.translation["n"+str(self.new_index+1)] = np.append(ui.translation["n"+str(self.new_index+1)], value)
            ui.translation_last["n"+str(self.new_index+1)] = value

def receiving_thread(name):

    global client, thread_exit
    for i in range(len(ui.topics)):
        client.subscribe("TSB/SR03/" + ui.topics[i])

    client.loop_start()

    while 1:
        if thread_exit == 1:
            return 
        else:
            time.sleep(1)

def on_message(client, userdata, message):
    
    global dataset, key_dict, names_or
    
    message_json = message.payload.decode("utf-8")
    try:
        parsed_json = json.loads(message_json)
        json_keys = list(parsed_json.keys())
        success =  1
        
    except:
        success = 0

    if success:   
        for key in json_keys[:-1]:
            value = float(parsed_json[key])
  
            if key not in key_dict:
                for i in range(len(ui.plot_objects)):
                    ui.plot_objects[i].plotted.append(0)
                key_dict[key] = (len(key_dict))
                new_signal = time_value_pair(key, [time.time()-start_time, value], 'Arroba')
                dataset.signal.append(new_signal)
                ui.translation["n"+str(len(key_dict))] = np.array([dataset.signal[key_dict[key]].value])
                ui.translation_last["n"+str(len(key_dict))] = value
                names_or.append("n"+str(len(key_dict)) +":"+ dataset.signal[key_dict[key]].name)
                for i in range(len(ui.plot_objects)):
                    ui.plot_objects[i].names.append("n"+str(len(key_dict)) +":"+ dataset.signal[key_dict[key]].name)
                    ui.plot_objects[i].comboBox.addItem("n"+str(len(key_dict)) +":"+ dataset.signal[key_dict[key]].name)
            else:
                dataset.signal[key_dict[key]].update(time.time() - start_time, value)
                ui.translation["n" + str(key_dict[key]+1)] = np.append(ui.translation["n" + str(key_dict[key]+1)], value)
                ui.translation_last["n" + str(key_dict[key]+1)] = value

        
                
        for i in range(len(ui.new_signals)):
            ui.new_signals[i].update()
	    
def on_connect(client, userdata, flags, rc):

    ui.label.setText("Connected with result code "+str(rc))
    ui.statusbar_timer = time.time()

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):

        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("View Data")

        global names_or, dataset
        self.follow = 0

        self.time_window = 10
        self.translation = {}
        self.translation_last = {}
        self.new_signals = []
        self.plot_objects = []
        self.statusbar_timer = 0

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        for i in range(4):
            self.plot_objects.append(plot_obj())
            if i > 0:
                self.plot_objects[i].graphicsView.setXLink(self.plot_objects[0].graphicsView)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)

        self.bar = self.menubar.addMenu('Edit')
        self.DarkMode = QtWidgets.QAction('Dark Mode', MainWindow)
        self.DarkMode.setShortcut('ctrl+d')
        self.bar.addAction(self.DarkMode)
        self.DarkMode.triggered.connect(self.DarkWhiteMode)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setFont(QtGui.QFont("Arial", 12))

        self.real_mode = 'white'


        self.new_plot_label = QtWidgets.QLabel(self.centralwidget)
        self.new_plot_label.setText('New op, format: Op, name')
        self.new_plot_line = QtWidgets.QLineEdit(self.centralwidget)

        self.real_samples = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.real_samples.setEnabled(True)
        self.real_samples.setMaximum(60)
        self.real_samples.setValue(10)
        self.real_samples.valueChanged.connect(self.real_samples_update)

        self.new_plot_line.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.new_plot_line.returnPressed.connect(self.NewOperation)

        self.autoscaleX = QtWidgets.QPushButton(self.centralwidget)
        self.autoscaleX.setText("Follow\Autoscale X")
        self.autoscaleX.clicked.connect(self.follow_func)

        self.timer = QtCore.QTimer(self.centralwidget)
        self.timer.timeout.connect(self.UpdateLabel)    
        self.timer.start(2500)

        self.colors = [(255,0,0), (0,255,0), (0,0,255),(255,255,0), (255,0,255), (0,255,255),(255,128,0),(255,0,127)]

        for i in range(0,250):
            self.colors.append([random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])

        self.newGraph = QtWidgets.QPushButton(self.centralwidget)
        self.newGraph.setText("Add Graph")
        self.newGraph.clicked.connect(self.newGraphfunc)

        self.delGraph = QtWidgets.QPushButton(self.centralwidget)
        self.delGraph.setText("Erase Graph")
        self.delGraph.clicked.connect(self.deleteGraphfunc)

        LoadFile = QtWidgets.QAction('Load File', MainWindow)
        LoadFile.setShortcut('ctrl+l')
        self.bar.addAction(LoadFile)
        LoadFile.triggered.connect(self.LoadFileFunc)

        self.Connect = QtWidgets.QAction('Connect to mqtt', MainWindow)
        self.Connect.setShortcut('ctrl+c')
        self.bar.addAction(self.Connect)
        self.Connect.triggered.connect(self.Connect_func)

        MainWindow.setMenuBar(self.menubar)
        self.statusbar.addWidget(self.label)
        MainWindow.setStatusBar(self.statusbar)

        self.layout = QtWidgets.QGridLayout(self.centralwidget)

        self.layout.addWidget(self.new_plot_label,0,0,1,1)
        self.layout.addWidget(self.new_plot_line,0,1,1,1) 
        self.layout.addWidget(self.autoscaleX,0,2,1,1)
        self.layout.addWidget(self.newGraph,0,3,1,1)
        self.layout.addWidget(self.delGraph,0,4,1,1)
        self.layout.addWidget(self.real_samples,0,5,1,1)
         
        self.DarkWhiteMode()
        self.updateLayout(1)

        self.centralwidget.setLayout(self.layout)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        MainWindow.showFullScreen()
        MainWindow.showMaximized()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

    def real_samples_update(self):

        self.time_window = self.real_samples.value()

    def DarkWhiteMode(self):
        if(self.real_mode == 'white'):
            MainWindow.setStyleSheet(load_stylesheet())
            for i in range(len(self.plot_objects)):
                self.plot_objects[i].comboBox.setStyleSheet(load_stylesheet())
                self.plot_objects[i].autoscale.setStyleSheet(load_stylesheet())
                self.plot_objects[i].clear.setStyleSheet(load_stylesheet())
            self.DarkMode.setText("White Mode")
            self.label.setStyleSheet(load_stylesheet())
            self.real_mode = 'black'
            self.statusbar.setStyleSheet(load_stylesheet())
            self.new_plot_label.setStyleSheet(load_stylesheet())
            self.new_plot_line.setStyleSheet(load_stylesheet())
            self.autoscaleX.setStyleSheet(load_stylesheet())
            self.menubar.setStyleSheet(load_stylesheet())
            self.newGraph.setStyleSheet(load_stylesheet())
            self.delGraph.setStyleSheet(load_stylesheet())
            
        else:
            MainWindow.setStyleSheet("")
            self.DarkMode.setText("Dark Mode")
            self.real_mode = 'white'
            for i in range(len(self.plot_objects)):
                self.plot_objects[i].comboBox.setStyleSheet("")
                self.plot_objects[i].autoscale.setStyleSheet("")
                self.plot_objects[i].clear.setStyleSheet("")
            self.label.setStyleSheet("")
            self.new_plot_label.setStyleSheet("")
            self.new_plot_line.setStyleSheet("")
            self.autoscaleX.setStyleSheet("")
            self.menubar.setStyleSheet("")
            self.newGraph.setStyleSheet("")
            self.delGraph.setStyleSheet("")

    def follow_func(self):

        global Real_time

        if Real_time == 1:
            self.follow = 1
        else:
            for j in range(len(self.plot_objects)):
                self.plot_objects[j].graphicsView.enableAutoRange(axis='x')
                self.plot_objects[j].graphicsView.setAutoVisible(x=True)

    def NewOperation(self):

        text_split =self.new_plot_line.text().split(',')  
        if (len(text_split) < 2):
            self.new_plot_label.setText('Wrong Format') 
            self.timer.stop()
            self.timer.start(2500)
            return
        name = text_split[1]
        exp = text_split[0]

        if "n"+str(len(dataset.signal)) +":"+ name not in names_or:
            try:
                value = ne.evaluate(exp, self.translation)
            except Exception as e:
                self.timer.stop()
                self.timer.start(2500)
                self.new_plot_label.setText(str(e)) 

            found = []
            for key in self.translation:
                if key in exp:
                    found.append(key)
           
            for i in range(len(self.plot_objects)):
                    self.plot_objects[i].plotted.append(0)

            index = int(max(found, key=len).split("n")[1])         
            dataset.signal.append(time_value_pair(name, [dataset.signal[index].time, value], dataset.signal[index].unit))

            self.translation["n"+str(len(dataset.signal))] = np.array(dataset.signal[-1].value)
            self.new_signals.append(new_signal(exp, index, len(dataset.signal)-1))
            names_or.append("n"+str(len(dataset.signal)) +":"+ name)
            for i in range(len(self.plot_objects)):
                self.plot_objects[i].names.append("n"+str(len(dataset.signal)) +":"+ name)
                self.plot_objects[i].comboBox.addItem("n"+str(len(dataset.signal)) +":"+ name)
            self.new_plot_line.setText('')
            
        else:
            self.timer.stop()
            self.timer.start(2500)
            self.new_plot_label.setText('Já existe')            

    def UpdateLabel(self):     
        self.new_plot_label.setText('New op, format: Op, name')

    def Connect_func(self):

        global x, client, Real_time, thread_exit, key_dict, dataset

        if Real_time == 0:

            inp = QtWidgets.QInputDialog(self.centralwidget)
            inp.setInputMode(QtWidgets.QInputDialog.TextInput)
            inp.setTextValue("AHRS, foils, bms, motor1, motor2, throttle")

            if self.real_mode != 'white':
                inp.setStyleSheet(load_stylesheet())

            inp.setWindowTitle('')
            inp.setLabelText('Insert mqtt topics to subscribe:')

            if inp.exec_() != QtWidgets.QDialog.Accepted:
                return

            ui.follow = 1
            key_dict = {}
            dataset.signal.clear()
            self.reset_plots()
            Real_time = 1
            thread_exit = 0
            broker_address="tsb1.vps.tecnico.ulisboa.pt" 
            client_id = f'DataApp-{random.randint(0,1000)}'
            client = mqtt.Client(client_id) #create new instance - cena random
            client.on_connect = on_connect
            client.on_message = on_message
            client.username_pw_set('TSB', password='tecnicosb2020')
            client.connect(broker_address, 1883, 60) #connect to broker
            
            self.topics = inp.textValue().split(',')

            x = threading.Thread(target=receiving_thread, args=(1,))
            x.start()

            self.update_timer = QtCore.QTimer(self.centralwidget)
            self.update_timer.timeout.connect(self.update)
            self.update_timer.start(200)
            self.Connect.setText('Disconnect from mqtt')
            self.autoscaleX.setText('Follow')

        else:

            self.update_timer.stop()
            client.loop_stop()
            client.disconnect()
            thread_exit = 1
            Real_time = 0
            ui.follow = 0
            ui.label.setText("Disconnected from mqtt")
            ui.statusbar_timer = time.time()
            self.Connect.setText('Connect to mqtt')
            self.autoscaleX.setText('Follow/Autoscale X')
            
    def LoadFileFunc(self):

        global dataset, names_or

        if Real_time == 1:
            msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "", "Data will be lost\n Are you sure?",buttons= QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
            if self.real_mode != 'white':
                msgBox.setStyleSheet(load_stylesheet())
            msgBox.exec_()
            reply = msgBox.standardButton(msgBox.clickedButton())
            if reply != QtWidgets.QMessageBox.Yes:
                return

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.bar,"QFileDialog.getOpenFileName()", "","*.mat", options=options)

        if not fileName:
            return
        try:
            dataset = get_data(fileName)
        except Exception as e:
            self.label.setText(str(e))
            self.statusbar_timer = time.time()
            return

        if Real_time == 1:
            self.Connect_func()

        self.reset_plots()
        self.autoscaleX.setText('Autoscale X')

        for i in range(len(dataset.signal)):
            names_or.append("n"+str(i) +":"+ dataset.signal[i].name)
            self.translation["n"+str(i)] = dataset.signal[i].value

        for i in range(len(self.plot_objects)):
            for j in range(len(dataset.signal) + 100):
                self.plot_objects[i].plotted.append(0)
            self.plot_objects[i].names = names_or.copy()
            self.plot_objects[i].comboBox.addItems(names_or)

    def update(self):
        for i in range(len(self.plot_objects)):
            self.plot_objects[i].update()

    def newGraphfunc(self):

        self.plot_objects.append(plot_obj())
        for j in range(len(dataset.signal) + 100):
            self.plot_objects[-1].plotted.append(0)
        self.plot_objects[-1].names = names_or.copy()
        self.plot_objects[-1].comboBox.addItems(names_or)
        self.plot_objects[-1].graphicsView.setXLink(self.plot_objects[0].graphicsView)
        self.updateLayout(2)

    def deleteGraphfunc(self):

        if len(self.plot_objects) > 1:
            self.plot_objects.pop()
            self.updateLayout(3)

    def updateLayout(self, mode):

        if mode == 3:
            for i in reversed(range(4)):
                self.layout.itemAt(self.layout.count()-1-i).widget().setParent(None)
        else:
            row = 1
            col = 1
            i = 0
            ori = []
            ori.append([row, col])
            over = 0
            while i < len(self.plot_objects)-1:
                col = col + 1
                for j in range(1, row+1):
                    ori.append([j,col])
                    i=i+1
                    if i > len(self.plot_objects)-2:
                        over = 1
                        break
                        
                if over == 1:
                    break
                row = row + 1
                for j in range(1,col+1):
                    ori.append([row,j])
                    i=i+1
                    if i > len(self.plot_objects)-2:
                        break

            if(mode == 1):
                for i in range(len(self.plot_objects)):
                    self.layout.addWidget(self.plot_objects[i].autoscale, 1 + 2*(ori[i][0]-1),3*(ori[i][1]-1),1,1)
                    self.layout.addWidget(self.plot_objects[i].clear, 1 + 2*(ori[i][0]-1), 3*(ori[i][1]-1)+1,1,1)
                    self.layout.addWidget(self.plot_objects[i].comboBox, 1 + 2*(ori[i][0]-1), 3*(ori[i][1]-1)+2,1,1)
                    if len(self.plot_objects) == 1:
                        self.layout.addWidget(self.plot_objects[i].graphicsView, 2*(ori[i][0]), 3*(ori[i][1]-1), 1,6)
                    else:
                        self.layout.addWidget(self.plot_objects[i].graphicsView, 2*(ori[i][0]), 3*(ori[i][1]-1), 1,3)

            elif(mode == 2):
                self.layout.addWidget(self.plot_objects[len(self.plot_objects)-1].autoscale, 1 + 2*(ori[-1][0]-1),3*(ori[-1][1]-1),1,1)
                self.layout.addWidget(self.plot_objects[len(self.plot_objects)-1].clear, 1 + 2*(ori[-1][0]-1), 3*(ori[-1][1]-1)+1,1,1)
                self.layout.addWidget(self.plot_objects[len(self.plot_objects)-1].comboBox, 1 + 2*(ori[-1][0]-1), 3*(ori[-1][1]-1)+2,1,1)
                self.layout.addWidget(self.plot_objects[-1].graphicsView, 2*(ori[-1][0]), 3*(ori[-1][1]-1), 1,3)

    def max_func(self,list, pos):
        max = 0
        for i in range(len(list)):
            aux = list[i][pos]
            if aux > max:
                max = aux
        return max

    def reset_plots(self):

        global names_or

        self.translation = {}
        self.translation_last = {}
        self.new_signals = []
        names_or = []

        for j in range(len(self.plot_objects)):

            self.plot_objects[j].comboBox.clear()

            for index in self.plot_objects[j].plot_index:
                self.plot_objects[j].graphicsView.removeItem(self.plot_objects[j].plot[self.plot_objects[j].plot_index.index(index)])

            self.plot_objects[j].init_variables()

def service_shutdown():

    if Real_time == 1:
        global thread_exit
        global client
        client.loop_stop()
        client.disconnect()
        thread_exit = 1

    sys.exit(0)

if __name__ == "__main__":

    import sys

    thread_exit = 0
    Real_time = 0
    start_time = time.time()
    dataset = dataset_obj()
    key_dict = {}
    names_or = []
    app = QtWidgets.QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal_handler)

    app.aboutToQuit.connect(service_shutdown) # myExitHandler is a callable

    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    sys.exit(app.exec_())
