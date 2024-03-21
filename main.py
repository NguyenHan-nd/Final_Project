import sys
from time import sleep
import traceback
import cv2
from GUIver2_fixlayoutUI import Ui_MainWindow
from LoginUI import Ui_LoginUI
from load_dataUI import Ui_LoadData
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox
)
import check
from pyzbar.pyzbar import decode
import serial
import serial.tools.list_ports
import os
import Img_Process
import sqlite3


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress_img = pyqtSignal(object)
    progress_ReadFromArduino = pyqtSignal(int)
    progress_SendToArduino = pyqtSignal(int)
    progress_ProcessImg = pyqtSignal()



class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.Stop = False

        # Add the callback to our kwargs
        self.kwargs['progress_img'] = self.signals.progress_img
        self.kwargs['progress_ReadFromArduino'] = self.signals.progress_ReadFromArduino
        self.kwargs['progress_SendToArduino'] = self.signals.progress_SendToArduino
        self.kwargs['progress_ProcessImg'] = self.signals.progress_ProcessImg

    @pyqtSlot()
    def run(self):
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class Window(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicksCount = 0
        self.setupUi(self)
        self.setWindowTitle("Phần mềm chấm điểm trắc nghiệm tự động")
        self.CamID = 0
        self.kernel = [(3,3), (5,5)]
        self.COM_list = []
        self.StudentID = []
        self.CodeExam = []
        self.StudentAns = []
        self.path_db_Student = './database/Student.db'
        self.path_db_Exam = './database/QuanLyKyThi.db'
        self.path_db_Result = './database/TongHopKetQua.db'


        try:
            self.connectExam = sqlite3.connect(self.path_db_Exam)
            sql_MaMonHoc = """
                    SELECT 
                        MaMonHoc 
                    FROM
                        MonHoc
            """
            cur = self.connectExam.execute(sql_MaMonHoc)
            MaMonHoc = cur.fetchall()
            for k in MaMonHoc:
                self.cbx_MaMonHoc.addItem(k[0])
            sql_MaKythi = """
                    SELECT 
                        MaKyThi
                    FROM 
                        KyThi
            """
            cur = self.connectExam.execute(sql_MaKythi)
            MaKythi = cur.fetchall()
            for k in MaKythi:
                self.cbx_MaKyThi.addItem(k[0])

        except sqlite3.Error as e:
            #print(e)
            self.addTextScroll("Lỗi kết nối dữ liệu vào database")


        self.Btn_ON.clicked.connect(self.ON_CAM)
        self.Btn_OFF.clicked.connect(self.OFF_CAM)
        self.Btn_OFF.setEnabled(False)
        self.Btn_xemketqua.clicked.connect(self.DataView)
        self.Btn_Check.clicked.connect(self.Check_Database)


        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            self.COM_list.append(p.name)
        self.COM_list.sort()
        self.cbx_COM.clear()
        self.cbx_COM.addItems(self.COM_list)
        self.qtimer_search = QTimer(self)
        self.qtimer_Camera = QTimer(self)
        self.qtimer_search.timeout.connect(self.search_COM)
        self.qtimer_search.start(2000)
        self.cbx_Camera.addItems(['0','1','2'])


        self.Btn_Start.clicked.connect(self.Start_Program)
        self.Btn_Stop.clicked.connect(self.Stop_Program)
        self.Btn_Stop.setEnabled(False)

        self.Btn_Connect.clicked.connect(self.Connect_COM)
        self.Btn_Disconnect.clicked.connect(self.Disconnect_COM)
        self.Btn_Connect.setEnabled(True)
        self.Btn_Disconnect.setEnabled(False)

        self.Number = 0

        #Flag
        self.active_cam = 0
        self.Check_Img_Flag = 0

        self.test_flag = 0

        self.thread_pool = QThreadPool()
        self.Worker_ReadArduino = Worker(self.Read_From_Arduino_Exe)
        self.LoadData = LoadData()

        # self.actionExit.triggered.connect(self.close)

    def closeEvent(self, event):
        #print("event")
        reply = QMessageBox.question(self, 'Thông báo',
                                           "Bạn có muốn thoát không?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.active_cam = 0
            event.accept()
        else:
            event.ignore()

    def addTextScroll(self,s):
        self.listWidget.addItem("-------------------------------")
        self.listWidget.addItem(s)
        self.listWidget.scrollToBottom()

    def search_COM(self):
        ports = list(serial.tools.list_ports.comports())
        COM_list = list()
        for p in ports:
            COM_list.append(p.name)
        COM_list.sort()
        if COM_list != self.COM_list:
            self.COM_list = COM_list
            self.cbx_COM.clear()
            self.cbx_COM.addItems(self.COM_list)

    def Connect_COM(self):
        COM_port = self.cbx_COM.currentText()
        Baudrate = int(self.cbx_BAUD.currentText())

        try:
            self.DataSerial = serial.Serial(COM_port, Baudrate)
            #print("Connect clicked")
            self.Btn_Connect.setEnabled(False)
            self.Btn_Disconnect.setEnabled(True)
            self.addTextScroll("Kết nối {}, Baudrate {} thành công".format(COM_port, str(Baudrate)))

        except:
            self.addTextScroll("Kết nối {}, Baudrate {} bị lỗi.".format(COM_port, str(Baudrate)))
            pass

    def Disconnect_COM(self):
        #print("Disconnect clicked")

        try:
            self.DataSerial.close()
            self.Btn_Connect.setEnabled(True)
            self.Btn_Disconnect.setEnabled(False)
            self.addTextScroll("Ngắt kết nối cổng {} thành công". format(self.DataSerial.name))
        except:
            self.addTextScroll("Ngắt kết nối cổng {} bị lỗi". format(self.DataSerial.name))

    def RunCam(self, progress_img=None, progress_SendToArduino = None,progress_ReadFromArduino = None, progress_ProcessImg = None):
        cap = cv2.VideoCapture(self.CamID)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)
        while self.active_cam:
            ret,cv2_img = cap.read()
            if (ret):
                progress_img.emit(cv2_img)
                if (self.Check_Img_Flag == 1):
                    # Check QRCode
                    end_flag = 0
                    for a in decode(cv2_img):
                        if (a.data.decode('utf-8') == 'END'):
                            # END
                            end_flag = 1
                            self.Check_Img_Flag = 0
                            # self.send_Arduino_signal.emit(2)
                            # self.Image_Process_signal.emit()
                            #print("change")

                            self.Worker_ReadArduino.Stop = True
                            self.Process_Image()
                            break
                    if (end_flag == 1):
                        #print("End")
                        self.Check_Img_Flag = 0
                        self.active_cam = 0

                    # Check 4 Corners
                    for k in self.kernel:
                        if (check.check_image(cv2_img,k[0],k[1]) == 1):
                            #save
                            self.Number += 1
                            self.Check_Img_Flag = 0
                            cv2.imwrite('Image_Capture_New/' + str(self.Number) + '.jpg', cv2_img)
                            #send signal to Arduino
                            #print("Sent! arduino")
                            progress_SendToArduino.emit(1)
                            break


        cap.release()

    def ShowCam(self,cv_img):
        Image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        cv_img = cv2.flip(cv_img, 1)
        h, w, ch = Image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(Image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(480, 360, Qt.KeepAspectRatio)

        self.lb_Cam.setPixmap(QtGui.QPixmap.fromImage(p))
    def Process_Image_Exe(self,progress_img=None, progress_SendToArduino = None,progress_ReadFromArduino = None, progress_ProcessImg = None):
        #print('Image_Process')
        self.addTextScroll("Bắt đầu xử lý ảnh bài thi")
        folder_path = './Image_Capture_New/';

        for file in os.listdir(folder_path):
            curr_path = os.path.join(folder_path, file)
            image = cv2.imread(curr_path)
            z = 0
            flag = 0
            for k in self.kernel:
                z = z + 1
                if (z == len(self.kernel)): flag = 1
                a, b, c = Img_Process.Process(image, k[0], k[1], flag)

                if (a != 0 and b != 0 and c != 0):
                    self.StudentID.append(a)
                    self.StudentAns.append(b)
                    self.CodeExam.append(c)
                    break

        self.addTextScroll("Kết thúc xử lý ảnh bài thi")
        self.Database_Process()
    def Database_Process(self):
        self.addTextScroll("Xuất kết quả chấm vào database")
        try:
            Connect_Student = sqlite3.connect(self.path_db_Student)
            Connect_Exam = sqlite3.connect(self.path_db_Exam)
            Connect_Result = sqlite3.connect(self.path_db_Result)
            MaMonHoc = self.cbx_MaMonHoc.currentText()
            MaKyThi = self.cbx_MaKyThi.currentText()
            TenBangCham = self.Line_TenBangCham.text()
            sql_clear = """DROP TABLE IF EXISTS {};""".format(TenBangCham)
            sql_create = """
                                 CREATE TABLE {}
                                    (
                                        ID CHAR(6) PRIMARY KEY ,
                                        HoVaTen   NVARCHAR(30)  ,
                                        Lop         NVARCHAR(30) ,
                                        MaMon      NVARCHAR (6) ,
                                        MaKyThi   NVARCHAR (6) ,
                                        SoCauDung INT ,
                                        Diem        REAL        
                                    );
                                """.format(TenBangCham)
            #print(sql_create)
            Connect_Result.execute(sql_clear)
            #print(1)
            Connect_Result.execute(sql_create)
            #print(2)

            NumOfStudent = len(self.StudentID)

            i = 0
            while (i < NumOfStudent):
                ID = ''
                Code = ''
                Name = ''
                Class = ''
                for z in self.StudentID[i]:
                    ID += str(z)
                #print(ID)
                StuAns = self.StudentAns[i]
                for z in self.CodeExam[i]:
                    Code += str(z)
                #print(Code)
                sql_infor = """SELECT ID, NAME, Class FROM STUDENT_INFOR WHERE ID = '{}';""".format(ID)

                cursor = Connect_Student.execute(sql_infor)
                if len(cursor.fetchall()) == 0:
                    os.replace("./Image_Result/{}.png".format(ID), "./Fault/SaiID/{}.png".format(ID))
                    i += 1
                else:
                    cursor = Connect_Student.execute(sql_infor)
                    for row_number, row_data in enumerate(cursor):
                        Name = row_data[1]
                        Class = row_data[2]

                    sql_Ans = """select Cau, DapAn from TongHopDapAnThi
                                          WHERE MaMonThi = '{}' and MaKyThi = '{}' and MaDeThi = '{}'
                                          ORDER BY Cau ASC;""".format(MaMonHoc, MaKyThi, Code)
                    #print(sql_Ans)
                    cursorAns = Connect_Exam.execute(sql_Ans)
                    No = 0
                    Score = 0
                    CauDung = 0

                    if len(cursorAns.fetchall()) == 0:
                        os.replace("./Image_Result/{}.png".format(ID), "./Fault/SaiMaDe/{}.png".format(ID))
                        i += 1
                        ##print(11111)
                    else:
                        cursorAns = Connect_Exam.execute(sql_Ans)
                        for row_number, row_data in enumerate(cursorAns):
                            AnsChar = None
                            if (StuAns[No] == 0):
                                AnsChar = 'A'
                            elif (StuAns[No] == 1):
                                AnsChar = 'B'
                            elif (StuAns[No] == 2):
                                AnsChar = 'C'
                            elif (StuAns[No] == 3):
                                AnsChar = 'D'
                            #print(row_data[1])
                            if (AnsChar == row_data[1]): CauDung += 1
                            No += 1

                        Score = 10 * CauDung / (No)

                        sql_Add = """INSERT INTO {} (ID, HoVaTen, Lop, MaMon, MaKyThi, SoCauDung, Diem )
                                             VALUES ('{}', '{}', '{}', '{}', '{}', {}, {:.2f}); 
                                        """.format(TenBangCham,ID, Name, Class, MaMonHoc, MaKyThi, CauDung, Score)
                        #print(sql_Add)
                        new_cursor = Connect_Result.execute(sql_Add)
                        Connect_Result.commit()
                        i += 1
            Connect_Student.close()
            Connect_Exam.close()
            Connect_Result.close()
            #print("Done")
            self.addTextScroll("Xuất ra database thành công")
            self.addTextScroll("Kết thúc")
        except sqlite3.Error as e:
            #print(e)
            self.addTextScroll("Lỗi kết nối dữ liệu vào database")

    def Process_Image(self):
        worker = Worker(self.Process_Image_Exe)
        worker.signals.finished.connect(self.EndProgram)
        self.thread_pool.start(worker)

    def ON_CAM(self):
        self.Btn_ON.setEnabled(False)
        self.active_cam = 1
        self.CamID = int(self.cbx_Camera.currentText())
        self.lb_Cam.show()
        self.Btn_OFF.setEnabled(True)

        worker = Worker(self.RunCam)
        worker.signals.progress_img.connect(self.ShowCam)
        worker.signals.progress_SendToArduino.connect(self.Send_To_Arduino)
        worker.signals.finished.connect(lambda: self.Btn_ON.setEnabled(True))
        worker.signals.finished.connect(lambda: self.Btn_OFF.setEnabled(False))

        self.thread_pool.start(worker)

    def OFF_CAM(self):
        self.active_cam = 0
        self.lb_Cam.hide()

    def Start_Program(self):
        self.Number = 0

        self.Check_Img_Flag = 1

        self.Check_Img = 1

        self.COM_list = []
        self.StudentID = []
        self.CodeExam = []
        self.StudentAns = []

        if (self.Btn_Connect.isEnabled()):
            self.addTextScroll("Chưa kết nối cổng COM")


        else:
            self.Btn_Start.setEnabled(False)
            self.Btn_Stop.setEnabled(True)
            self.Read_From_Arduino()
            if (self.active_cam == 0):
                self.ON_CAM()

    def EndProgram(self):
        #print("EndProgram")
        #print(self.test_flag)
        self.Stop_Program()


    def Stop_Program(self):
        self.Btn_Start.setEnabled(True)
        self.Btn_Stop.setEnabled(False)
        self.Disconnect_COM()

    def Read_From_Arduino_Exe(self, progress_img=None, progress_SendToArduino = None,progress_ReadFromArduino = None, progress_ProcessImg = None):

        try:
            while (self.Worker_ReadArduino.Stop == 0):
                data = self.DataSerial.readline()
                data = data.decode('utf-8')
                data = data.strip('\r\n')
                if (data == "22"):
                    progress_ReadFromArduino.emit(1)
                data = ""

                if (self.Worker_ReadArduino.Stop):
                    #print("NgatArduino")
                    break
        except:
            pass
        self.test_flag = 1

    def Continue_Capture(self,x):
        if (x == 1):
            self.Check_Img_Flag = 1
            #print("Continue")

    def Read_From_Arduino(self):
        self.Worker_ReadArduino.Stop = False
        self.Worker_ReadArduino = Worker(self.Read_From_Arduino_Exe)
        self.Worker_ReadArduino.signals.progress_ReadFromArduino.connect(self.Continue_Capture)
        self.thread_pool.start(self.Worker_ReadArduino)

    def Send_To_Arduino(self,x):
        if (x == 1):
            data = str(x) + '\r'
            self.DataSerial.write(data.encode())
            #print("Send_Arduino")
    def Check_Database(self):
        sql_check = """
                SELECT 
                    MaMonThi, MaKyThi, MaDeThi
                FROM TongHopDapAnThi
                WHERE MaMonThi = "{}" AND MaKyThi = "{}";
        """.format(self.cbx_MaMonHoc.currentText(), self.cbx_MaKyThi.currentText())
        cur = self.connectExam.execute(sql_check)
        MaMonThi = cur.fetchall()

        if (len(MaMonThi) == 0):
            self.addTextScroll("Chưa tạo đáp án bài thi")
        elif (self.Line_TenBangCham.text() == ""):
            self.addTextScroll("Chưa nhập tên bảng chấm")
        else:
            self.addTextScroll("Không có lỗi xảy ra")
        cur.close()

    def DataView(self):
        self.LoadData.show()

class LoadData(QMainWindow, Ui_LoadData):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Xem kết quả chấm")

        self.tableWidget.setColumnCount(7)
        self.tableWidget.setColumnWidth(0, 70)
        self.tableWidget.setColumnWidth(1, 150)
        self.tableWidget.setColumnWidth(2, 70)
        self.tableWidget.setColumnWidth(3, 70)
        self.tableWidget.setColumnWidth(4, 70)
        self.tableWidget.setColumnWidth(5, 100)
        self.tableWidget.setColumnWidth(6, 100)
        self.tableWidget.setHorizontalHeaderLabels(
            ['ID', 'Họ và tên', 'Lớp', 'Mã môn', 'Mã kỳ thi', 'Số câu đúng', 'Điểm'])

        self.pushButton.clicked.connect(self.LoadData)
        self.Btn_Refresh.clicked.connect(self.Refresh_Tablelist)

        self.Refresh_Tablelist()
    def Refresh_Tablelist(self):
        self.comboBox.clear()
        connect = sqlite3.connect('./database/TongHopKetQua.db')
        cur = connect.cursor()
        sql_query = """
                    SELECT name FROM sqlite_schema 
                    WHERE type IN ('table','view') 
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY 1;
        """
        for row in cur.execute(sql_query):
            self.comboBox.addItem(row[0])
        cur.close()

    def LoadData(self):
        self.tableWidget.clearContents()
        connection = sqlite3.connect('./database/TongHopKetQua.db')
        cur = connection.cursor()
        sql_query = """
                    SELECT * FROM {}
                """.format(self.comboBox.currentText())
        self.tableWidget.setRowCount(100)

        tableRow = 0
        for row in cur.execute(sql_query):
            for i in range(0, len(row)):
                item = QtWidgets.QTableWidgetItem(str(row[i]))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                if (i != 1): item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(tableRow, i, item)
                self.tableWidget.setItemDelegateForRow(i, None)

            tableRow += 1
        cur.close()

class Login(QMainWindow, Ui_LoginUI):
    def __init__(self):
        super(Login,self).__init__()
        self.setupUi(self)
        self.MainWindow = Window()
        self.setWindowTitle("Đăng nhập")
        self.Btn_login.clicked.connect(self.GoMain)

    def GoMain(self):
        try:
            Connect_UserDB = sqlite3.connect("./database/User.db")
            username = self.Line_Username.text()
            password = self.Line_Password.text()

            # #print(username, password)

            sql_select = """
                    SELECT 
                        username
                    FROM USER
                    WHERE username = "{}" AND password = "{}" ;
            """.format(username, password)
            cur = Connect_UserDB.execute(sql_select)
            Connect_UserDB.commit()
            if len(cur.fetchall()) == 1:
                msg_Login_Success = QMessageBox()
                msg_Login_Success.setIcon(QMessageBox.Information)
                msg_Login_Success.setText("Đăng nhập thành công")
                msg_Login_Success.setWindowTitle("Thông báo")
                msg_Login_Success.setStandardButtons(QMessageBox.Ok)
                msg_Login_Success.exec_()

                if msg_Login_Success.buttonClicked:
                    LoginUI_scr.close()
                    self.MainWindow.show()
                    LoginUI_scr.close()
                    return
            elif len(cur.fetchall()) == 0:
                msg_Login_Fail = QMessageBox()
                msg_Login_Fail.setIcon(QMessageBox.Critical)
                msg_Login_Fail.setText("Tài khoản hoặc mật khẩu không đúng ! Vui lòng kiểm tra !")
                msg_Login_Fail.setWindowTitle("Thông báo")
                msg_Login_Fail.setStandardButtons(QMessageBox.Ok)
                msg_Login_Fail.exec_()


        except sqlite3.Error as e:

            msg_Login_Fail = QMessageBox()
            msg_Login_Fail.setIcon(QMessageBox.Critical)
            msg_Login_Fail.setText(str(e))
            msg_Login_Fail.setWindowTitle("Thông báo")
            msg_Login_Fail.setStandardButtons(QMessageBox.Ok)
            msg_Login_Fail.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    LoginUI_scr = Login()
    LoginUI_scr.show()
    app.exec()