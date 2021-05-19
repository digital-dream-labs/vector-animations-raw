import os
import re
import maya.cmds as mc
from subprocess import *
from fcntl import *
import signal

try:
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *
except ImportError:
    from PySide.QtWidgets import *
    from PySide.QtCore import *
    from PySide.QtGui import *

_maya_version = mc.about(version=True).split()[0]
VECTOR_SETTINGS_PATH = os.path.join(os.getenv("HOME"), ".anki", "maya", _maya_version, ".vector_settings")

TOOLS_DIR_ENV_VAR = "ANKI_TOOLS"

TOOLS_OTHER_DIR = os.path.join(os.getenv(TOOLS_DIR_ENV_VAR), "other")

OPEN_MAC_CLIENT_SHELL_SCRIPT = os.path.join(TOOLS_OTHER_DIR, "open_mac_client.sh")

CONNECT_TO_MAC_CLIENT_CMD = OPEN_MAC_CLIENT_SHELL_SCRIPT + " {0}"

OTA_VECTOR_CMD = os.path.join(TOOLS_OTHER_DIR, "ota_update.sh") + " {0}"

MAC_CLIENT_DIR = os.path.join(TOOLS_OTHER_DIR, "mac-client")

CONNECT_TO_ANKI_WIFI_CMD = MAC_CLIENT_DIR + " --filter {0} -p 2 -s 'wifi-scan; @robits; wifi-ip;'"

CONNECT_TO_SETTINGS_WIFI_CMD = MAC_CLIENT_DIR + " --filter {0} -p 2 -s 'wifi-scan; wifi-connect:{1}|{2}; wifi-ip'"

TIME_OUT_MS = 40 * 1000

WIFI_STARTING_MSG = "Connecting Vector to the internet..."

MAC_CLIENT_TIMEOUT_MSG = "Timed out: Try to connect to mac-client again."

GENERAL_TIMEOUT_MSG = "Timed out: Could not complete mac-client action."

LOADING_GIF = os.path.join(TOOLS_OTHER_DIR, "ajax-loader.gif")

# Regular Expression to find '###.###.###.###' IP Address pattern
IP_ADDRESS_REGEX = r"[0-9]+(?:\.[0-9]+){3}"


# Enum for mac-client modes
class MacClientMode:
    MAC_CLIENT, WIFI, OTA = range(3)


class VectorSettingsStruct:
    vector_id = ""
    is_using_anki_robits = False
    wifi_id = ""
    wifi_pass = ""


class MacClientThread(QThread):
    def __init__(self, settings, qDialog, macClientMode):
        QThread.__init__(self)
        self.vectorSettings = settings
        self.startTime = QTime.currentTime()
        self.mac_client_process = None
        self.parentDialog = qDialog
        self.robot_pin = 0
        self.running = True
        self.mode = macClientMode
        self.success = False

        if self.mode is MacClientMode.MAC_CLIENT:
            self.cmd = CONNECT_TO_MAC_CLIENT_CMD.format(self.vectorSettings.vector_id)
        elif self.mode is MacClientMode.WIFI:
            if self.vectorSettings.is_using_anki_robits:
                self.cmd = CONNECT_TO_ANKI_WIFI_CMD.format(self.vectorSettings.vector_id)
            else:
                self.cmd = CONNECT_TO_SETTINGS_WIFI_CMD.format(self.vectorSettings.vector_id,
                                                               self.vectorSettings.wifi_id,
                                                               self.vectorSettings.wifi_pass)
        elif self.mode is MacClientMode.OTA:
            self.cmd = OTA_VECTOR_CMD.format(self.vectorSettings.vector_id)

    def __del__(self):
        self.terminate()

    def _get_process(self):
        killall_proc = Popen("killall -9 mac-client".split())
        self.sleep(1)
        killall_proc.kill()

        process = Popen(self.cmd, stdout=PIPE, stdin=PIPE, shell=True, preexec_fn=os.setsid)
        print("Running cmd: " + self.cmd)

        return process

    def process_mac_client(self):
        print("Starting mac-client process.")
        self.mac_client_process = self._get_process()
        while self.running:
            line = self.mac_client_process.stdout.readline().rstrip()
            if not line:
                break
            yield line

    def run(self):
        for process_output in self.process_mac_client():
            if self.mode is MacClientMode.WIFI:
                if "IPv4:" in process_output:
                    ip_address = re.findall(IP_ADDRESS_REGEX, process_output)[0]
                    if ip_address:
                        wifi_name = self.vectorSettings.wifi_id
                        if self.vectorSettings.is_using_anki_robits:
                            wifi_name = "AnkiRobits"
                        self.print_to_output("Your Vector is connected to the {0} WiFi!".format(wifi_name))
                        self.print_to_output("\nHere is its IP Address: {0}".format(ip_address))
                        self.emit(SIGNAL('set_robot_ip(QString)'), ip_address)
                        self.success = True
            else:
                self.print_to_output(process_output)
        print("Thread done")
        if self.mac_client_process.poll is None:
            self.mac_client_process.kill()

    def set_robot_pin(self, robot_pin):
        self.robot_pin = robot_pin
        self.mac_client_process.stdin.write(str(self.robot_pin))
        print("\nInserting robot's pin: " + str(self.robot_pin))

    def print_to_output(self, str):
        self.emit(SIGNAL('print_to_output(QString)'), str)

    def kill_process(self):
        try:
            os.killpg(os.getpgid(self.mac_client_process.pid), signal.SIGINT)
        except OSError:
            print("\nProcess does not exist anymore.")
        except AttributeError:
            pass
        self.running = False


class MacClientDialog(QDialog):
    def __init__(self, parent, macClientMode):
        super(MacClientDialog, self).__init__(parent)
        self.vectorSettings = parent.getVectorSettingsStruct()
        self.robot_ip_line_edit = parent.robotID
        self.thread_finished = False
        self.mode = macClientMode
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(600)

        vbox = QVBoxLayout(self)
        vbox.setAlignment(Qt.AlignVCenter)
        self.loadingLabel = QLabel()
        self.loadingGif = QMovie(LOADING_GIF)
        self.loadingLabel.setMovie(self.loadingGif)
        self.loadingGif.start()

        self.textOutput = QTextEdit()
        self.textOutput.setReadOnly(True)
        self.textOutput.setFrameStyle(QFrame.NoFrame)

        vbox.addWidget(self.textOutput)
        vbox.addWidget(self.loadingLabel)

        if not self.vectorSettings.vector_id:
            QMessageBox.warning(self, "No Vector ID", "Please save your Vector ID in the Vector Settings.")
        else:
            self._start_thread()

    def _start_thread(self):
        if self.mode is MacClientMode.MAC_CLIENT:
            self.setWindowTitle("Vector to mac-client")
            self.print_to_output("Connecting Vector to mac-client...")
        elif self.mode is MacClientMode.WIFI:
            if not self.vectorSettings.is_using_anki_robits:
                if not self.vectorSettings.wifi_id or not self.vectorSettings.wifi_pass:
                    QMessageBox.warning(self, "No WiFi Info",
                                        "In Vector Settings, please check the 'Use AnkiRobits' checkbox or "
                                        "fill in the 'WiFi ID' and 'WiFi Password' field.")
                    return

            self.setWindowTitle("Vector to WiFi")
            self.print_to_output(WIFI_STARTING_MSG)
        elif self.mode is MacClientMode.OTA:
            self.setWindowTitle("OTA Vector")

        self.show()
        self.macClientThread = MacClientThread(self.vectorSettings, self, self.mode)
        self._setup_signals()

        self.macClientThread.start()

        self._set_timeout(TIME_OUT_MS)

    def _setup_signals(self):
        self.connect(self.macClientThread, SIGNAL("print_to_output(QString)"), self.print_to_output)
        self.connect(self.macClientThread, SIGNAL("finished()"), self.finish)
        self.connect(self.macClientThread, SIGNAL("set_robot_ip(QString)"), self.set_robot_ip)
        self.connect(self.macClientThread, SIGNAL("pin()"), self.ask_for_vector_id)

    def set_robot_ip(self, ip_address):
        self.robot_ip_line_edit.setText(ip_address)

    def _setup_timer_to_prompt_for_robot_pin(self):
        self.pin_timer = QTimer(self)
        self.pin_timer.setSingleShot(True)
        self.connect(self.pin_timer, SIGNAL("timeout()"), self.ask_for_vector_id)
        self.pin_timer.start(3000)

    def _set_timeout(self, milliseconds):
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.connect(self.timeout_timer, SIGNAL("timeout()"), self.timeout)
        self.timeout_timer.start(milliseconds)

    def timeout(self):
        if not self.thread_finished:
            if self.mode is MacClientMode.MAC_CLIENT:
                self.print_to_output(MAC_CLIENT_TIMEOUT_MSG)
            else:
                self.print_to_output(GENERAL_TIMEOUT_MSG)
            self.macClientThread.kill_process()

    def print_to_output(self, str):
        self.textOutput.append(str)

    def finish(self):
        self.thread_finished = True
        self.loadingGif.stop()
        self.loadingLabel.hide()
        self.macClientThread.terminate()
        if (self.mode is MacClientMode.WIFI) and (not self.macClientThread.success):
            self.print_to_output("Could not connect to WiFi."
                                 "\nMake sure you can connect Vector to mac-client and have 'anki-auth'd your Vector.")
        self.print_to_output("You can close this window now.")
        print("\nDeleted thread.")

    def closeEvent(self, *args, **kwargs):
        try:
            self.macClientThread.kill_process()
        except AttributeError:
            pass
        print("\nClosed dialog window.")

    def ask_for_vector_id(self):
        robot_pin, ok_pressed = QInputDialog.getText(self, "Robot PIN", "Enter your robot's PIN:", QLineEdit.Normal, "")
        if ok_pressed and robot_pin != '':
            self.macClientThread.set_robot_pin(int(robot_pin))
            return True
        return False


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.setWindowTitle("Vector Settings")
        self.setMinimumWidth(500)

        # Holds the settings_horizontal_container_layout and the buttons vertically.
        vbox = QVBoxLayout(self)

        # Holds the label_layouts and settings_layouts horizontally.
        settings_horizontal_container_layout = QHBoxLayout()

        # Vertical layout that holds all the Label texts on the left hand side.
        label_layouts = QVBoxLayout()

        # Vertical layout that holds all the editable widgets on the right hand side.
        settings_layouts = QVBoxLayout()

        # Vector ID.
        vector_id_label = QLabel("Vector ID")
        self.vector_id = QLineEdit("")
        self.vector_id.setMaximumWidth(40)

        # Python Server Host Directory.
        # python_hosting_dir_label = QLabel("Python Server Directory")
        # self.python_hosting_dir = QLineEdit("")

        # WiFi
        wifi_id_label = QLabel("WiFi ID")
        self.wifi_id = QLineEdit("")
        self.wifi_id.setMaximumWidth(220)

        anki_robits_checkbox_label = QLabel("Use AnkiRobits")
        self.anki_robits_checkbox = QCheckBox()
        self.anki_robits_checkbox.stateChanged.connect(self.__toggle_wifi_field)

        wifi_id_password_label = QLabel("WiFi Password")
        self.wifi_password_field = QLineEdit("")
        self.wifi_password_field.setMaximumWidth(220)
        self.wifi_password = ""

        # Fills in the fields for the settings.
        self.__load_settings()

        # If no Vector Settings file exists, make these values default.
        if not os.path.exists(VECTOR_SETTINGS_PATH):
            self.anki_robits_checkbox.setChecked(True)
            # self.python_hosting_dir.setText(os.path.join(os.path.expanduser('~'), 'Downloads'))

        # Add all the labels for settings.
        label_layouts.addWidget(vector_id_label)
        label_layouts.addWidget(wifi_id_label)
        label_layouts.addWidget(anki_robits_checkbox_label)
        label_layouts.addWidget(wifi_id_password_label)
        # label_layouts.addWidget(python_hosting_dir_label)

        # The text field and the file selection button for Python Server Hosting.
        # python_hosting_dir_h_layout = QHBoxLayout()
        #
        # find_dir_button = QPushButton()
        # find_dir_button.setText("...")
        # find_dir_button.clicked.connect(self.__choose_ota_directory)
        #
        # python_hosting_dir_h_layout.addWidget(self.python_hosting_dir)
        # python_hosting_dir_h_layout.addWidget(find_dir_button)

        # Add all the widgets for settings.
        settings_layouts.addWidget(self.vector_id)
        settings_layouts.addWidget(self.wifi_id)
        settings_layouts.addWidget(self.anki_robits_checkbox)
        settings_layouts.addWidget(self.wifi_password_field)
        # settings_layouts.addLayout(python_hosting_dir_h_layout)

        settings_horizontal_container_layout.addLayout(label_layouts)
        settings_horizontal_container_layout.addLayout(settings_layouts)

        # Buttons.
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.__save_settings_and_close)
        cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        vbox.addLayout(settings_horizontal_container_layout)
        vbox.addLayout(buttons_layout)

        save_button.setFocus()

    def __choose_ota_directory(self):
        dir = str(QFileDialog.getExistingDirectory(self, caption="Select Python SimpleHTTPServer Directory"))
        if dir:
            self.python_hosting_dir.setText(dir)

    def __toggle_wifi_field(self):
        if self.anki_robits_checkbox.isChecked():
            self.wifi_id.setEnabled(False)
            self.wifi_password_field.setEnabled(False)
        else:
            self.wifi_id.setEnabled(True)
            self.wifi_password_field.setEnabled(True)

    def __save_settings_and_close(self):
        self.__save_settings()
        self.close()

    def __save_settings(self):
        self.vector_id.setText(self.vector_id.text().upper())
        settings = QSettings(VECTOR_SETTINGS_PATH, QSettings.IniFormat)
        settings.beginGroup("vector")
        settings.setValue("vector_id", self.vector_id.text())
        settings.setValue("wifi_id", self.wifi_id.text())
        if not bool(re.match('^[*]+$', self.wifi_password_field.text())):
            self.wifi_password = self.wifi_password_field.text()
            settings.setValue("wifi_pass", self.wifi_password_field.text())
            self.wifi_password_field.setText(str(settings.value("wifi_pass")).__len__() * '*')
        settings.setValue("use_anki_robits", self.anki_robits_checkbox.isChecked())
        settings.endGroup()

    def __load_settings(self):
        settings = QSettings(VECTOR_SETTINGS_PATH, QSettings.IniFormat)
        settings.beginGroup("vector")
        self.vector_id.setText(settings.value("vector_id"))
        self.wifi_id.setText(settings.value("wifi_id"))
        self.wifi_password = settings.value("wifi_pass")
        self.wifi_password_field.setText(str(settings.value("wifi_pass")).__len__() * '*')
        self.anki_robits_checkbox.setChecked(bool(settings.value("use_anki_robits")))
        settings.endGroup()

    def set_vector_id(self, new_id):
        self.vector_id.setText(new_id.upper())
        settings = QSettings(VECTOR_SETTINGS_PATH, QSettings.IniFormat)
        settings.beginGroup("vector")
        settings.setValue("vector_id", self.vector_id.text().upper())
        settings.endGroup()

    def get_vector_id(self):
        return self.vector_id.text()

    def set_python_server_dir(self, new_dir):
        self.python_hosting_dir.setText(new_dir)
        settings = QSettings(VECTOR_SETTINGS_PATH, QSettings.IniFormat)
        settings.beginGroup("vector")
        settings.setValue("python_server_dir", self.python_hosting_dir.text())
        settings.endGroup()

    def get_python_server_dir(self):
        return self.python_hosting_dir.text()

    def get_wifi_id(self):
        return self.wifi_id.text()

    def get_wifi_pass(self):
        return self.wifi_password

    def is_using_anki_robits(self):
        return self.anki_robits_checkbox.isChecked()
