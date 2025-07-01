import numpy as np
import qtawesome as qta
from lys.Qt import QtWidgets, QtGui, QtCore


class SingleMotorGUI(QtWidgets.QGroupBox):
    """
    Graphical user interface (GUI) for controlling a single-axis motor device.

    Provides a control panel for a `SingleMotorInterface` instance, allowing users to:
        - View the current position
        - Set a target position
        - Start and stop motion
        - Access device settings
        - Toggle digital connections
    
    The GUI updates automatically in response to state changes from the motor backend.

    Attributes:
        _obj (SingleMotorInterface): The motor interface object to control.
        _nowAt (QDoubleSpinBox): Displays the current motor position (read-only).
        _moveTo (QDoubleSpinBox): Allows the users to enter and view the target position value.
        _execute (QPushButton): Button to start the motor motion to the target position.
        _interrupt (QPushButton): Button to stop the motor motion.
        _aliveStateIndicator (QLabel): Shows the current alive/dead status of the motor.

    Public Methods:
        settingsWidget(parent=None): Returns a settings dialog (overrides `SingleMotorInterface.settingsWidget(parent=None)`).
    
    Private Methods:
        _busyStateChanged(busy): Slot to update the GUI in response to busy state changes.
        _aliveStateChanged(alive): Slot to update the GUI in response to alive state changes.
        _showSettings(): Opens the settings dialog for the device.
    """

    def __init__(self, obj, title):
        """
        Initializes the SingleMotorGUI.

        Args:
            obj (SingleMotorInterface): The motor interface object to control.
            title (str): The title to display on the control panel.
        """
        super().__init__(title)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setFont(QtGui.QFont(self.font().family(), 12))
        self._obj = obj
        self.__initLayout()

        self._obj.valueChanged.connect(self._nowAt.setValue)
        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)
        

    def __initLayout(self):
        """
        Creates and initializes all GUI components of the control panel, and connects signals to their respective slots.
        """
        self.setStyleSheet('QDoubleSpinBox {'
                           'font-size: 18pt;'
                           '}'
                           'QPushButton {'
                           'font-size: 15pt;'
                           '}'
                           'QLabel {'
                           'font-size: 12pt;'
                           '}')
        self._nowAt = QtWidgets.QDoubleSpinBox()
        self._nowAt.setValue(self._obj.get())
        self._nowAt.setRange(-np.inf, np.inf)
        self._nowAt.setReadOnly(True)
        self._nowAt.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
        nowAtText = QtWidgets.QLabel('Now at')

        self._moveTo = QtWidgets.QDoubleSpinBox()
        self._moveTo.setValue(self._obj.get())
        self._moveTo.setRange(-np.inf, np.inf)
        moveToText = QtWidgets.QLabel('Move to')

        self._execute = QtWidgets.QPushButton('Go', clicked=lambda: self._obj.set(self._moveTo.value()))    # Toggle wait = True / False
        self._execute.setEnabled(True)

        self._interrupt = QtWidgets.QPushButton('Stop', clicked=self._obj.stop)
        self._interrupt.setEnabled(False)

        self._aliveStateIndicator = QtWidgets.QLabel()
        self._aliveStateChanged(self._obj.isAlive())
        
        settingsIcon = QtWidgets.QPushButton(qta.icon('ri.settings-5-fill'), '', clicked=self._showSettings)
        settingsIcon.setToolTip('Settings')
        settingsIcon.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        settingsIcon.setStyleSheet('min-width: 16px;'
                                   'min-height: 16px;'
                                   'max-width: 48px;'
                                   'max-height: 48px;')

        # self._obj.valueChanged.connect(self._nowAt.setValue)
        # self._obj.busyStateChanged.connect(self._busyStateChanged)
        # self._obj.aliveStateChanged.connect(self._aliveStateChanged)
        
        gl = QtWidgets.QGridLayout()
        gl.addWidget(nowAtText, 0, 0)
        gl.addWidget(moveToText, 0, 1)
        gl.addWidget(self._nowAt, 1, 0)
        gl.addWidget(self._moveTo, 1, 1)
        gl.addWidget(self._interrupt, 2, 0)
        gl.addWidget(self._execute, 2, 1)
        gl.addWidget(settingsIcon, 2, 2, alignment=QtCore.Qt.AlignCenter)
        gl.addWidget(self._aliveStateIndicator, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(gl)

    def _busyStateChanged(self, busy):
        """
        Updates the control panel in response to changes in the motor's busy/idle status.

        Args:
            busy (bool): True if the motor is moving, False otherwise.
        """
        self._execute.setEnabled(not busy and self._obj.isAlive())
        self._interrupt.setEnabled(busy and self._obj.isAlive())
        if busy:
            self._execute.setText('Moving')
        else:
            self._execute.setText('Go')
    
    def _aliveStateChanged(self, alive):
        """
        Updates the control panel in response to changes in the motor's alive/dead status.

        Args:
            alive (bool): True if the motor is responsive, False otherwise.
        """
        self._execute.setEnabled(not self._obj.isBusy() and alive)
        self._interrupt.setEnabled(self._obj.isBusy() and alive)
        color = '#adff2f' if alive else '#ff0000'
        self._aliveStateIndicator.setText('Alive' if alive else 'Dead')
        self._aliveStateIndicator.setStyleSheet(f'background-color: {color};'
                                                # 'font-size: 18pt;'
                                                'border-radius: 8px;'
                                                'min-width: 16px;'
                                                'min-height: 16px;'
                                                'max-width: 48px;'
                                                'max-height: 48px;'
                                                'padding-left: 2px;'
                                                'padding-right: 2px;'
                                                'padding-top: 2px;'
                                                'padding-bottom: 2px;')

    def _showSettings(self):
        """
        Opens the settings dialog for the device.
        """
        self.settingsWidget(parent=self).open()

    def settingsWidget(self, parent=None):
        """
        Returns a settings dialog for the device.

        Args:
            parent (QWidget, optional): Parent widget for the dialog.

        Returns:
            QDialog: The settings dialog for the device.
        """
        return _settingsDialog(self._obj, parent)
    


class _settingsDialog(QtWidgets.QDialog):
    """
    Settings dialog for a single-axis motor device.

    Provides a dialog window to view and toggle the motor's alive/dead status.
    The dialog stays synchronized with the parent control panel.

    Attributes:
        _obj (SingleMotorInterface): The motor object whose settings are being managed.
        _aliveLineEdit (QLineEdit): Displays the current alive/dead status of the motor.

    Methods:
        _initLayout(): Initializes the layout and GUI components of the dialog.
        _toggleAlive(): Toggles the motor's alive/dead state and emits the corresponding signal.
        _setAliveState(): Updates the displayed alive/dead status in the dialog.
    """

    def __init__(self, obj, parent):
        """
        Initializes the settings dialog.

        Args:
            obj (SingleMotorInterface): The motor object whose settings are being managed.
            parent (QWidget): The parent widget for this dialog.
        """
        super().__init__(parent=parent)
        self.setWindowTitle('Settings - SingleMotorDummy')
        self._obj = obj
        self._initLayout()

    def _initLayout(self):
        """
        Creates and initializes all GUI components of the settings dialog, and connects signals to their respective slots.
        """
        toggleAlive = QtWidgets.QPushButton('Change', clicked=self._toggleAlive)

        self._aliveLineEdit = QtWidgets.QLineEdit('Alive')
        self.setStyleSheet('QLineEdit {border-radius: 13px;'
                           'font-size: 15pt;'
                           'border: 0px;'
                           '}')
        self._aliveLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self._setAliveState()
        self._obj.aliveStateChanged.connect(self._setAliveState)

        gl = QtWidgets.QGridLayout()
        gl.addWidget(toggleAlive, 0, 0)
        gl.addWidget(self._aliveLineEdit, 1, 0)
        self.setLayout(gl)

    def _toggleAlive(self):
        """
        Toggles the alive/dead state of the motor and emits the corresponding signal.
        """
        self._obj._alive = not self._obj.isAlive()
        self._obj.aliveStateChanged.emit(self._obj._alive)

    def _setAliveState(self):
        """
        Updates the displayed alive/dead status in the dialog.
        """
        if self._obj.isAlive():
            self._aliveLineEdit.setText('Alive')
            self._aliveLineEdit.setStyleSheet('background-color: #adff2f; color: #000000')
        else:
            self._aliveLineEdit.setText('Dead')
            self._aliveLineEdit.setStyleSheet('background-color: #ff0000; color: #ffffff')



if __name__ == '__main__':              # To Test the GUI run in the src\python: python -m fstem.lys_instr.GUI.SingleMotorGUI
    import sys
    from fstem.lys_instr import SingleMotorDummy
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    dummy = SingleMotorDummy()
    gui = SingleMotorGUI(dummy, 'Single Motor Control')
    gui.show()
    sys.exit(app.exec_())

