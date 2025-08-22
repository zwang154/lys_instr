import numpy as np
import qtawesome as qta
import pyqtgraph as pg
import logging

from lys.Qt import QtWidgets, QtGui, QtCore
from lys import multicut
from lys.widgets import LysSubWindow

logging.basicConfig(level=logging.INFO)


class MultiDetectorGUI(QtWidgets.QWidget):
    """
    GUI for MultiDetectorInterface.
    Only for implementation in lys.
    """

    def __init__(self, obj, wait=False, output=False, parent=None):
        super().__init__(parent)
        self._obj = obj
        self._wait = wait
        self._output = output
        self._mode = None  # "acquire", "stream", or None
        self._frameCount = 0

        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.dataAcquired.connect(self._dataAcquired)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)

        self._initLayout()

    def _initLayout(self):
        # Data display widget
        self._mcut = multicut(np.random.rand(*self._obj._frameDim), returnInstance=True, subWindow=False)
        self._mcut.widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Acquisition control widgets
        self._expTime = QtWidgets.QDoubleSpinBox()
        self._expTime.setValue(self._obj._frameTime)
        self._expTime.setRange(0, np.infty)
        self._expTime.setDecimals(3)
        self._expTime.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._expTime.valueChanged.connect(self._onExposureChanged)

        exposeLabel = QtWidgets.QLabel("Exp. (s)")
        exposeLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._acquire = QtWidgets.QPushButton("Acquire", clicked=self._onAcquireClicked)
        self._stream = QtWidgets.QPushButton("Stream", clicked=self._onStreamClicked)
        self._stop = QtWidgets.QPushButton("Stop", clicked=self._onStopClicked)
        self._stop.setEnabled(False)

        settings = QtWidgets.QPushButton(qta.icon("ri.settings-5-fill"), "", clicked=self._showSettings)
        settings.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        settings.setIconSize(QtCore.QSize(24, 24))

        self._aliveIndicator = QtWidgets.QLabel()
        icon = qta.icon("ri.checkbox-circle-fill", color="green") if self._obj.isAlive else qta.icon("ri.close-circle-fill", color="red")
        self._aliveIndicator.setPixmap(icon.pixmap(24, 24))
        self._aliveIndicator.setAlignment(QtCore.Qt.AlignCenter)
        self._aliveIndicator.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # Layout setup
        imageLayout = QtWidgets.QHBoxLayout()
        imageLayout.addWidget(self._mcut.widget)

        controlsLayout = QtWidgets.QHBoxLayout()
        controlsLayout.addWidget(self._aliveIndicator)
        controlsLayout.addWidget(exposeLabel)
        controlsLayout.addWidget(self._expTime)
        controlsLayout.addWidget(self._acquire)
        controlsLayout.addWidget(self._stream)
        controlsLayout.addWidget(self._stop)
        controlsLayout.addWidget(settings)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(imageLayout, stretch=1)
        mainLayout.addLayout(controlsLayout, stretch=0)
        
        self.setLayout(mainLayout)

    def _onAcquireClicked(self):
        self._obj._numFrames = np.prod(self._obj.indexDim)
        self._mode = "acquire"
        self._data = np.zeros(self._obj.dataShape)
        self._mcut.cui.setRawWave(self._data)
        self._obj.startAcq(wait=self._wait, output=self._output)

    def _onStreamClicked(self):
        self._obj._numFrames = None
        self._mode = "stream"
        self._data = np.zeros(self._obj.dataShape)
        self._mcut.cui.setRawWave(self._data)

        # Need to leave wait=False for streaming
        self._obj.startAcq(wait=False, output=self._output)

    def _dataAcquired(self, data):
        busy = self._obj.isBusy
        alive = self._obj.isAlive
        self._stream.setEnabled(not busy and alive)
        self._acquire.setEnabled(not busy and alive)
        self._stop.setEnabled(busy)

        if data:
            for idx, frame in data.items():
                self._data[idx[-frame.ndim:]] = frame
            self._frameCount += 1

            # Update frame display every N frames or on last frame
            updateInterval = int(self._updateInterval.text())
            if self._frameCount % updateInterval == 0 or self._frameCount == len(data):
                self._mcut.cui.setRawWave(self._data)
       
    def _onStopClicked(self):
        self._mode = None
        self._obj._frameCount = 0
        self._obj.stop()
        self._stream.setEnabled(True)
        self._acquire.setEnabled(True)
        self._stop.setEnabled(False)

    def _busyStateChanged(self, busy):
        alive = self._obj.isAlive
        self._stream.setEnabled(not busy and alive)
        self._acquire.setEnabled(not busy and alive)
        self._stop.setEnabled(busy)

        if busy:
            if self._mode == "acquire":
                self._acquire.setText("Acquiring")
            elif self._mode == "stream":
                self._stream.setText("Streaming")
        else:
            self._acquire.setText("Acquire")
            self._stream.setText("Stream")
            self._mode = None

    def _aliveStateChanged(self, alive):
        busy = self._obj.isBusy
        self._acquire.setEnabled(not busy and alive)
        self._acquire.setText("Acquiring" if busy else "Acquire")
        self._stream.setEnabled(not busy and alive)
        self._stream.setText("Streaming" if busy else "Stream")
        self._stop.setEnabled(busy)
        icon = qta.icon("ri.checkbox-circle-fill", color="green") if alive else qta.icon("ri.close-circle-fill", color="red")
        self._aliveIndicator.setPixmap(icon.pixmap(24, 24))

    def _onExposureChanged(self, value):
        self._obj._frameTime = value

    def _showSettings(self):
        generalTab = GeneralPanel(self._obj)
        optionsTab = OptionsPanel(wait=self._wait)

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(generalTab, "General")
        tabWidget.addTab(optionsTab, "Options")

        settingsWindow = LysSubWindow()
        settingsWindow.setWidget(tabWidget)
        settingsWindow.setWindowTitle("Detector Settings")
        # settingsWindow.adjustSize()
        settingsWindow.show()
        settingsWindow.adjustSize()

    def _onWaitCheckChanged(self, wait):
        self._wait = wait

    def _updateDisplay(self):
        self._frameCount = 0

    def _onScheduledUpdateCheckChanged(self, state):
        self._updateInterval.setEnabled(state)


# class _MultiDetectorGUI(QtWidgets.QGroupBox):

#     def __init__(self, obj, wait=False, output=False):
#         super().__init__(title="Multi-Detector Control")
#         self._obj = obj
#         self._image = np.zeros(obj.indexDim)
#         self._wait = wait
#         self._output = output
#         self._mode = None  # "acquire", "stream", or None
#         self._frameCount = 0

#         # Set title style
#         self.setAlignment(QtCore.Qt.AlignHCenter)
#         self.setFont(QtGui.QFont(self.font().family(), 12))

#         # Connect signals
#         self._obj.busyStateChanged.connect(self._busyStateChanged)
#         self._obj.dataAcquired.connect(self._dataAcquired)
#         self._obj.aliveStateChanged.connect(self._aliveStateChanged)

#         self._initLayout()

#     def _initLayout(self):
#         self.setStyleSheet("QLineEdit {font-size: 14pt}"
#                            "QDoubleSpinBox {font-size: 14pt}"
#                            "QPushButton {font-size: 12pt}"
#                            "QLabel {font-size: 12pt}")

#         # Widgets for data displaying
#         self._canvas = pg.ImageView()
#         self._canvas.ui.menuBtn.hide()
#         self._canvas.ui.roiBtn.hide()
#         self._canvas.setMinimumSize(500, 400)
#         # self._canvas.ui.histogram.hide()
#         self._frameView = pg.ImageView()
#         self._frameView.ui.menuBtn.hide()
#         self._frameView.ui.roiBtn.hide()
#         self._frameView.setMinimumSize(500, 400)
#         # self._frameView.ui.histogram.hide()

#         # Widgets for acquisition control
#         self._expTime = QtWidgets.QDoubleSpinBox()
#         self._expTime.setValue(self._obj._frameTime)
#         self._expTime.setRange(0, np.infty)
#         self._expTime.setDecimals(3)
#         self._expTime.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
#         self._expTime.valueChanged.connect(self._onExposureChanged)

#         exposeLabel = QtWidgets.QLabel("Exp. (s)")
#         exposeLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

#         self._acquire = QtWidgets.QPushButton("Acquire", clicked=self._onAcquireClicked)
#         self._stream = QtWidgets.QPushButton("Stream", clicked=self._onStreamClicked)
#         self._stop = QtWidgets.QPushButton("Stop", clicked=self._onStopClicked)
#         self._stop.setEnabled(False)

#         settings = QtWidgets.QPushButton(qta.icon("ri.settings-5-fill"), "", clicked=self._showSettings)
#         settings.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
#         settings.setIconSize(QtCore.QSize(24, 24))

#         self._aliveIndicator = QtWidgets.QLabel()
#         icon = qta.icon("ri.checkbox-circle-fill", color="green") if self._obj.isAlive else qta.icon("ri.close-circle-fill", color="red")
#         self._aliveIndicator.setPixmap(icon.pixmap(24, 24))
#         self._aliveIndicator.setAlignment(QtCore.Qt.AlignCenter)
#         self._aliveIndicator.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

#         # Create collapsible panel
#         self._collapsible = QtWidgets.QWidget()

#         self._expandBtn = QtWidgets.QToolButton()
#         self._expandBtn.setArrowType(QtCore.Qt.RightArrow)
#         self._expandBtn.setCheckable(True)
#         self._expandBtn.setChecked(False)
#         self._expandBtn.setAutoRaise(True)
#         self._expandBtn.setIconSize(QtCore.QSize(14, 14))
#         self._expandBtn.toggled.connect(self._onExpandBtnClicked)

#         expanderLine = QtWidgets.QFrame()
#         expanderLine.setFrameShape(QtWidgets.QFrame.HLine)
#         expanderLine.setStyleSheet("color: lightgray;")

#         # Create option panel
#         self._optionsPanel = QtWidgets.QWidget()
#         optionsPanelText = QtWidgets.QLabel("Options")

#         scheduledUpdateCheck = QtWidgets.QCheckBox("Scheduled update", checked=False)
#         scheduledUpdateCheck.stateChanged.connect(self._onScheduledUpdateCheckChanged)

#         updateIntervalTextBefore = QtWidgets.QLabel("Update display every")
#         self._updateInterval = QtWidgets.QSpinBox()
#         self._updateInterval.setEnabled(False)
#         self._updateInterval.setRange(1, 2**31 - 1)
#         self._updateInterval.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
#         updateIntervalTextAfter = QtWidgets.QLabel("frames")

#         updateBtn = QtWidgets.QPushButton("Update", clicked=self._updateDisplay)
#         updateBtn.setEnabled(True)



#         # Create collapsible panel
#         self._collapsible = QtWidgets.QWidget()

#         self._expandBtn = QtWidgets.QToolButton()
#         self._expandBtn.setArrowType(QtCore.Qt.RightArrow)
#         self._expandBtn.setCheckable(True)
#         self._expandBtn.setChecked(False)
#         self._expandBtn.setAutoRaise(True)
#         self._expandBtn.setIconSize(QtCore.QSize(14, 14))
#         self._expandBtn.toggled.connect(self._onExpandBtnClicked)

#         expanderLine = QtWidgets.QFrame()
#         expanderLine.setFrameShape(QtWidgets.QFrame.HLine)
#         expanderLine.setStyleSheet("color: lightgray;")

#         # option panel layout
#         updateLayout = QtWidgets.QHBoxLayout()
#         updateLayout.addWidget(scheduledUpdateCheck)
#         updateLayout.addWidget(updateIntervalTextBefore)
#         updateLayout.addWidget(self._updateInterval)
#         updateLayout.addWidget(updateIntervalTextAfter)
#         updateLayout.addWidget(updateBtn)

#         waitLayout = QtWidgets.QHBoxLayout()
#         self._waitCheck = QtWidgets.QCheckBox("Wait for acquisition to finish", checked=self._wait)
#         self._waitCheck.stateChanged.connect(self._onWaitCheckChanged)
#         waitLayout.addWidget(self._waitCheck)

#         optionsLayout = QtWidgets.QVBoxLayout(self._optionsPanel)
#         optionsLayout.addWidget(optionsPanelText)
#         optionsLayout.addLayout(updateLayout)
#         optionsLayout.addLayout(waitLayout)
#         self._optionsPanel.setVisible(False)


#         # Layout setup
#         imageLayout = QtWidgets.QHBoxLayout()
#         imageLayout.addWidget(self._canvas, stretch=1)
#         imageLayout.addWidget(self._frameView, stretch=1)

#         controlsLayout = QtWidgets.QHBoxLayout()
#         controlsLayout.addWidget(self._aliveIndicator)
#         controlsLayout.addWidget(exposeLabel)
#         controlsLayout.addWidget(self._expTime)
#         controlsLayout.addWidget(self._acquire)
#         controlsLayout.addWidget(self._stream)
#         controlsLayout.addWidget(self._stop)
#         controlsLayout.addWidget(settings)

#         collapsibleLayout = QtWidgets.QHBoxLayout(self._collapsible)
#         collapsibleLayout.setContentsMargins(0, 0, 0, 0)
#         collapsibleLayout.addWidget(self._expandBtn)
#         collapsibleLayout.addWidget(expanderLine)
#         collapsibleLayout.setStretch(1, 1)

#         mainLayout = QtWidgets.QVBoxLayout()
#         mainLayout.addLayout(imageLayout, stretch=1)
#         mainLayout.addLayout(controlsLayout, stretch=0)
#         mainLayout.addWidget(self._collapsible, stretch=0)
#         mainLayout.addWidget(self._optionsPanel, stretch=0)

#         self.setLayout(mainLayout)

#     def _browseDir(self):
#         dirStr = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", self._fileDir.text())
#         if dirStr:
#             self._fileDir.setText(dirStr)

#     def _onAcquireClicked(self):
#         self._obj._numFrames = np.prod(self._obj.indexDim)
#         self._mode = "acquire"
#         if self._wait:
#             self._busyStateChanged(True)
#             self._stop.setEnabled(False)
#             QtWidgets.QApplication.processEvents()
#         self._obj.startAcq(wait=self._wait, output=self._output)

#     def _onStreamClicked(self):
#         self._obj._numFrames = None
#         self._mode = "stream"
#         # Need to leave wait=False for streaming
#         self._obj.startAcq(wait=False, output=self._output)

#     def _onStopClicked(self):
#         self._mode = None
#         self._frameCount = 0
#         self._obj.stop()
#         self._stream.setEnabled(True)
#         self._acquire.setEnabled(True)
#         self._stop.setEnabled(False)

#     def _dataAcquired(self, data):
#         busy = self._obj.isBusy
#         alive = self._obj.isAlive
#         self._stream.setEnabled(not busy and alive)
#         self._acquire.setEnabled(not busy and alive)
#         self._stop.setEnabled(busy)

#         # Display logic: update image array with new frames
#         if data:
#             for idx, frame in data.items():
#                 self._image[idx[-2:]] = self._indexDisplay(frame)
#             self._frameCount += 1

#             # Update frame display every N frames or on last frame
#             updateInterval = int(self._updateInterval.text())
#             if self._frameCount % updateInterval == 0 or self._frameCount == len(data):
#                 self._frameView.setImage(self._frameDisplay(list(data.values())[-1]))
       
#         self._canvas.setImage(self._image)

#     def _busyStateChanged(self, busy):
#         alive = self._obj.isAlive
#         self._stream.setEnabled(not busy and alive)
#         self._acquire.setEnabled(not busy and alive)
#         self._stop.setEnabled(busy)

#         if busy:
#             if self._mode == "acquire":
#                 self._acquire.setText("Acquiring")
#             elif self._mode == "stream":
#                 self._stream.setText("Streaming")
#         else:
#             self._acquire.setText("Acquire")
#             self._stream.setText("Stream")
#             self._mode = None

#     def _aliveStateChanged(self, alive):
#         busy = self._obj.isBusy
#         self._acquire.setEnabled(not busy and alive)
#         self._acquire.setText("Acquiring" if busy else "Acquire")
#         self._stream.setEnabled(not busy and alive)
#         self._stream.setText("Streaming" if busy else "Stream")
#         self._stop.setEnabled(busy)
#         icon = qta.icon("ri.checkbox-circle-fill", color="green") if alive else qta.icon("ri.close-circle-fill", color="red")
#         self._aliveIndicator.setPixmap(icon.pixmap(24, 24))

#     def _onExposureChanged(self, value):
#         self._obj._frameTime = value

#     def _showSettings(self):
#         dialog = self.settingsWidget(parent=self)
#         dialog.open()

#     def _indexDisplay(self, data):
#         return np.mean(data) 
    
#     def _frameDisplay(self, frame):
#         return frame
    
#     def _onExpandBtnClicked(self, checked):
#         self._optionsPanel.setVisible(checked)
#         self._expandBtn.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
#         self.adjustSize()

#     def _onWaitCheckChanged(self, wait):
#         self._wait = wait

#     def _updateDisplay(self):
#         self._frameCount = 0

#     def _onScheduledUpdateCheckChanged(self, state):
#         self._updateInterval.setEnabled(state)

#     def settingsWidget(self, parent=None):
#         return _settingsDialog(self._obj, parent)



class GeneralPanel(QtWidgets.QWidget):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._obj = obj
        self._obj.aliveStateChanged.connect(self._updateAliveState)
        self._initLayout()

    def _initLayout(self):
        # Create alive panel
        self._switch = QtWidgets.QPushButton("Change", clicked=self._toggleAlive)
        # self._switch.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self._aliveLineEdit = QtWidgets.QLineEdit("Alive", alignment=QtCore.Qt.AlignCenter)

        self._aliveIndicator = QtWidgets.QLabel()
        alive = self._obj.isAlive
        icon = qta.icon("ri.checkbox-circle-fill", color="green") if alive else qta.icon("ri.close-circle-fill", color="red")
        self._aliveIndicator.setPixmap(icon.pixmap(24, 24))
        self._aliveIndicator.setAlignment(QtCore.Qt.AlignCenter)

        # aliveLayout = QtWidgets.QGridLayout()
        # aliveLayout.addWidget(self._switch, 0, 0)
        # aliveLayout.addWidget(self._aliveLineEdit, 1, 0, alignment=QtCore.Qt.AlignCenter)
        # aliveLayout.setRowStretch(0, 1)      # Makes row 0 stretchable
        # aliveLayout.setRowStretch(1, 1)      # Makes row 1 stretchable
        # aliveLayout.setColumnStretch(0, 1)   # Makes column 0 stretchable

        aliveLayout = QtWidgets.QVBoxLayout()
        aliveLayout.addStretch(1)
        aliveLayout.addWidget(self._switch, alignment=QtCore.Qt.AlignCenter)
        aliveLayout.addStretch(1)
        aliveLayout.addWidget(self._aliveLineEdit, alignment=QtCore.Qt.AlignCenter)
        aliveLayout.addStretch(1)

        # Combine layouts
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(aliveLayout)
        self.setLayout(mainLayout)

        # Initialize alive state  
        self._updateAliveState()
        
    def _toggleAlive(self):
        backend = self._obj
        backend._error = not backend._error
        if (data := backend._get()):                            # _get()
            backend.dataAcquired.emit(data)
        backend.aliveStateChanged.emit(backend.isAlive)

    def _updateAliveState(self):
        if self._obj.isAlive:
            self._aliveLineEdit.setText("Alive")
            self._aliveLineEdit.setStyleSheet("background-color: #adff2f; color: #000000")
        else:
            self._aliveLineEdit.setText("Dead")
            self._aliveLineEdit.setStyleSheet("background-color: #ff0000; color: #ffffff")


class OptionsPanel(QtWidgets.QWidget):
    def __init__(self, parent=None, wait=False):
        super().__init__(parent)

        scheduledUpdateCheck = QtWidgets.QCheckBox("Scheduled update")
        updateIntervalTextBefore = QtWidgets.QLabel("Update display every")
        updateInterval = QtWidgets.QSpinBox()
        updateInterval.setEnabled(False)
        updateInterval.setRange(1, 2**31 - 1)
        updateInterval.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        updateIntervalTextAfter = QtWidgets.QLabel("frames")

        updateBtn = QtWidgets.QPushButton("Update")
        waitCheck = QtWidgets.QCheckBox("Wait for acquisition to finish", checked=wait)

        # Connect signals internally
        scheduledUpdateCheck.stateChanged.connect(updateInterval.setEnabled)
        # Add more internal logic as needed

        updateLayout = QtWidgets.QHBoxLayout()
        updateLayout.addWidget(scheduledUpdateCheck)
        updateLayout.addWidget(updateIntervalTextBefore)
        updateLayout.addWidget(updateInterval)
        updateLayout.addWidget(updateIntervalTextAfter)
        updateLayout.addWidget(updateBtn)

        waitLayout = QtWidgets.QHBoxLayout()
        waitLayout.addWidget(waitCheck)

        optionsLayout = QtWidgets.QVBoxLayout(self)
        optionsLayout.addLayout(updateLayout)
        optionsLayout.addLayout(waitLayout)

        # Expose widgets if needed
        self.scheduledUpdateCheck = scheduledUpdateCheck
        self.updateInterval = updateInterval
        self.waitCheck = waitCheck



# To Test the GUI run in the src\python: python -m fstem.lys_instr.GUI.MultiDetectorGUI
if __name__ == "__main__":
    import sys
    from lys_instr.dummy.MultiDetector import MultiDetectorDummy
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    detector = MultiDetectorDummy(indexDim=(5, 5), frameDim=(256, 256), frameTime=0.1)
    gui = MultiDetectorGUI(detector, wait=False, output=False)
    gui.show()
    sys.exit(app.exec_())


# To test the GUI within lys: PS C:\Users\wzq19\src\test> python -m lys
# Within lys: g=test() -> Click Acquire -> Template -> OK -> Yes