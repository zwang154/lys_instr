import numpy as np
import qtawesome as qta
import os
import ast
from lys.Qt import QtWidgets, QtGui, QtCore


class MultiMotorGUI(QtWidgets.QGroupBox):
    def __init__(self, obj, title):
        super().__init__(title)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setFont(QtGui.QFont(self.font().family(), 12))
        self._obj = obj
        self._obj.valueChanged.connect(self._valueChanged)
        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)
        self._obj.valueSet.connect(self._valueSet)
        
        dir = os.path.join('.lys_instr', 'GUI', 'MultiMotor')
        os.makedirs(dir, exist_ok=True)
        self._path = os.path.join(dir, 'position_positionList.lst')
        if os.path.exists(self._path):
            with open(self._path, 'r') as f:
                txt = f.read()
                try:
                    self._namedPositions = ast.literal_eval(txt)
                except Exception:
                    self._namedPositions = []
        else:
            self._namedPositions = []
        
        self.__initLayout()
        self._updateMemory()

    def __initLayout(self):
        self.setStyleSheet('QLineEdit {font-size: 14pt}'
                           'QDoubleSpinBox {font-size: 14pt}'
                           'QPushButton {font-size: 12pt}'
                           'QLabel {font-size: 12pt}')

        self._nowAt = {name: QtWidgets.QDoubleSpinBox() for name in self._obj.getNames()}
        for dsb in self._nowAt.values():
            dsb.setRange(-np.inf, np.inf)
            dsb.setReadOnly(True)
            dsb.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
            dsb.setDecimals(3)
        nowAtText = QtWidgets.QLabel('Now at')

        self._moveTo = {name: QtWidgets.QLineEdit() for name in self._obj.getNames()}
        moveToText = QtWidgets.QLabel('Move to')

        self._jogNega = {name: QtWidgets.QPushButton(qta.icon('ri.arrow-left-fill'), '', clicked=self._nega) for name in self._obj.getNames()}
        for btn in self._jogNega.values():
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self._jogNegaReversed = {btn: name for name, btn in self._jogNega.items()}

        self._jogPosi = {name: QtWidgets.QPushButton(qta.icon('ri.arrow-right-fill'), '', clicked=self._posi) for name in self._obj.getNames()}
        for btn in self._jogPosi.values():
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self._jogPosiReversed = {btn: name for name, btn in self._jogPosi.items()}

        self._jogStep = {name: QtWidgets.QDoubleSpinBox() for name in self._obj.getNames()}
        for dsb in self._jogStep.values():
            dsb.setRange(0, np.inf)
            dsb.setDecimals(2)
        jogText = QtWidgets.QLabel('Jog')
        jogStepText = QtWidgets.QLabel('Step')

        self._execute = QtWidgets.QPushButton('Go', clicked=self._setMoveToValue)
        self._execute.setEnabled(True)

        self._interrupt = QtWidgets.QPushButton('Stop', clicked=self._obj.stop)
        self._interrupt.setEnabled(False)

        self._aliveStateIndicator = QtWidgets.QLabel()
        self._aliveStateChanged(self._obj.isAlive())

        settings = QtWidgets.QPushButton(qta.icon('ri.settings-5-fill'), '', clicked=self._showSettings)
        settings.setToolTip('Settings')
        settings.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        settings.setIconSize(QtCore.QSize(20, 24))

        self._positionList = QtWidgets.QTreeWidget()
        self._positionList.setColumnCount(3)
        self._positionList.setHeaderLabels(['Label', 'Position', 'Memo'])
        self._positionList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._positionList.itemSelectionChanged.connect(lambda: self._updateMemoryButtons(load, delete))
        self._positionList.setIndentation(0)
        self._positionList.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked)
        self._positionList.itemChanged.connect(self._memoEdited)
        self._positionList.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._positionList.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self._positionList.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self._positionList.setItemDelegateForColumn(0, NoEditDelegate(self._positionList))
        self._positionList.setItemDelegateForColumn(1, NoEditDelegate(self._positionList))


        self._memory = QtWidgets.QToolButton()
        self._memory.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self._memory.setIcon(qta.icon('ri.save-2-fill'))  # 'ri.bookmark-fill', 'ri.save-2-fill'
        self._memory.setCheckable(True)
        self._memory.setChecked(False)
        self._memory.setToolTip('Memory')
        self._memory.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self._memory.setIconSize(QtCore.QSize(24, 24))
        self._memory.toggled.connect(self._toggleMemoryTree)

        self._memoryPanel = QtWidgets.QWidget()
        # self._memoryPanel.setVisible(False)
        memoryPanelText = QtWidgets.QLabel('Memory')

        memoryPanelSeparator = QtWidgets.QFrame()
        memoryPanelSeparator.setFrameShape(QtWidgets.QFrame.HLine)
        memoryPanelSeparator.setStyleSheet('color: lightgray;')



        save = QtWidgets.QPushButton('Save', clicked=self._save)
        save.setEnabled(True)
        
        load = QtWidgets.QPushButton('Load', clicked=self._load)
        load.setEnabled(False)

        delete = QtWidgets.QPushButton('Delete', clicked=self._delete)
        delete.setEnabled(False)

        axisName = {name: QtWidgets.QLabel(name.replace('stage_', '')) for name in self._obj.getNames()}
        for lbl in axisName.values():
            lbl.setAlignment(QtCore.Qt.AlignCenter)
        axisText = QtWidgets.QLabel('Axis')


        gl = QtWidgets.QGridLayout()
        gl.addWidget(nowAtText, 0, 1)
        gl.addWidget(moveToText, 0, 2)
        gl.addWidget(jogText, 0, 3)
        gl.addWidget(jogStepText, 0, 5)
        gl.addWidget(axisText, 0, 0)
        for i, name in enumerate(self._obj.getNames()):
            gl.addWidget(axisName[name], 1 + i, 0)
            gl.addWidget(self._nowAt[name], 1 + i, 1)
            gl.addWidget(self._moveTo[name], 1 + i, 2)
            gl.addWidget(self._jogNega[name], 1 + i, 3)
            gl.addWidget(self._jogPosi[name], 1 + i, 4)
            gl.addWidget(self._jogStep[name], 1 + i, 5)
        gl.addWidget(self._interrupt, 1 + len(self._nowAt), 1)
        gl.addWidget(self._execute, 1 + len(self._nowAt), 2)
        gl.addWidget(self._aliveStateIndicator, 1 + len(self._nowAt), 3, alignment=QtCore.Qt.AlignCenter)
        gl.addWidget(settings, 1 + len(self._nowAt), 4, alignment=QtCore.Qt.AlignCenter)
        gl.addWidget(self._memory, 1 + len(self._nowAt), 5, alignment=QtCore.Qt.AlignRight)
        gl.addWidget(self._memoryPanel, 2 + len(self._nowAt), 0, len(self._obj.getNames()), 6)     # addWidget(widget, row, column, rowSpan, columnSpan)
        self.setLayout(gl)

        # Within memory panel
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(save)
        buttonLayout.addWidget(load)
        buttonLayout.addWidget(delete)

        memoryPanelLayout = QtWidgets.QVBoxLayout(self._memoryPanel)
        memoryPanelLayout.setContentsMargins(0, 0, 0, 0)
        memoryPanelLayout.addWidget(memoryPanelSeparator)
        memoryPanelLayout.addWidget(memoryPanelText)
        memoryPanelLayout.addWidget(self._positionList)
        memoryPanelLayout.addLayout(buttonLayout)
        self._memoryPanel.setVisible(False)


    def _setMoveToValue(self):        # Wrapper for self._obj.set(self._moveToValue())
        value = []
        for name in self._moveTo:
            text = self._moveTo[name].text()
            try:
                value.append(float(text))
            except ValueError:
                value.append(np.nan)
        self._obj.set(value)

    def _valueSet(self, valueList):
        for key, value in valueList.items():
            self._moveTo[key].setText(str(value))

    def _valueChanged(self, valueList):
        for key, value in valueList.items():
            self._nowAt[key].setValue(value)

    def _busyStateChanged(self, busy):
        self._execute.setEnabled(not busy and self._obj.isAlive())
        self._interrupt.setEnabled(busy and self._obj.isAlive())
        for btn in self._jogNega.values():
            btn.setEnabled(not busy and self._obj.isAlive())
        for btn in self._jogPosi.values():
            btn.setEnabled(not busy and self._obj.isAlive())
        if busy:
            self._execute.setText('Moving')
        else:
            self._execute.setText('Go')

    def _aliveStateChanged(self, alive):
        self._execute.setEnabled(not self._obj.isBusy() and alive)
        self._interrupt.setEnabled(self._obj.isBusy() and alive)
        for btn in self._jogNega.values():
            btn.setEnabled(not self._obj.isBusy() and alive)
        for btn in self._jogPosi.values():
            btn.setEnabled(not self._obj.isBusy() and alive)
        icon = qta.icon('ri.checkbox-circle-fill', color='green') if alive else qta.icon('ri.close-circle-fill', color='red')
        self._aliveStateIndicator.setPixmap(icon.pixmap(24, 24))

    def _nega(self):
        name = self._jogNegaReversed.get(self.sender())
        if name is not None:
            i = self._obj.getNames().index(name)
            value = self._obj.get()
            value[i] = value[i] - self._jogStep[name].value()  # Subtract for negative jog
            value[:i] = np.nan
            value[i + 1:] = np.nan
            self._obj.set(value)

    def _posi(self):
        name = self._jogPosiReversed.get(self.sender())
        if name is not None:
            i = self._obj.getNames().index(name)
            value = self._obj.get()
            value[i] = value[i] + self._jogStep[name].value()  # Add for positive jog
            value[:i] = np.nan
            value[i + 1:] = np.nan
            self._obj.set(value)

    # def _toggleMemoryTree(self, checked):
    #     self._positionList.setVisible(checked)
    #     if checked:
    #         self._showMemory.setText('Hide Memory')
    #     else:
    #         self._showMemory.setText('Show Memory')

    def _toggleMemoryTree(self, checked):
        self._memoryPanel.setVisible(checked)
        # self._memory.setArrowType(QtCore.Qt.UpArrow if checked else QtCore.Qt.DownArrow)
        self._memory.setIcon(qta.icon('ri.save-2-fill'))   # 'ri.bookmark-fill', 'ri.save-2-fill'
        self.adjustSize()  # This line ensures the window resizes to fit the new layout
        
    def _save(self):
        names = [name for name, *_ in self._namedPositions]
        i = 1
        while f'{i}' in names:
            i += 1
        newName = f'{i}'
        newPosition = list(self._obj.get())
        newMemo = ''
        self._namedPositions.append((newName, newPosition, newMemo))
        with open(self._path, 'w') as f:
            f.write(str(self._namedPositions))
        self._updateMemory()

    def _load(self):
        selections = [i.text(1) for i in self._positionList.selectedItems()]
        if selections:
            try:
                self._obj.set(ast.literal_eval(selections[0]))
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, 'Load Error', f'Could not load position:\n{e}')

    def _delete(self):
        selectedNames = {i.text(0) for i in self._positionList.selectedItems()}
        self._namedPositions = [item for item in self._namedPositions if item[0] not in selectedNames]
        try:
            with open(self._path, 'w') as f:
                f.write(str(self._namedPositions))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Delete Error', f'Could not update file:\n{e}')
        self._updateMemory()

    def _updateMemory(self):
        self._positionList.clear()      # _positionList is a QTreeWidget
        for name, position, memo in self._namedPositions:
            displayedPosition = ', '.join(f'{v:.3f}' for v in position)
            item = QtWidgets.QTreeWidgetItem([name, displayedPosition, memo])
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)  # This allows editing, but delegates block columns 0 and 1
            self._positionList.addTopLevelItem(item)
        for col in range(self._positionList.columnCount()):
            self._positionList.resizeColumnToContents(col)

    def _memoEdited(self, item, column):
        if column == 2:  # Memo column
            name = item.text(0)
            for idx, (n, pos, _) in enumerate(self._namedPositions):
                if n == name:
                    self._namedPositions[idx] = (n, pos, item.text(2))
                    with open(self._path, 'w') as f:
                        f.write(str(self._namedPositions))
                    break

    def _updateMemoryButtons(self, loadPushButton, deletePushButton):
        selected = len(self._positionList.selectedItems()) > 0
        loadPushButton.setEnabled(selected)
        deletePushButton.setEnabled(selected)

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


class NoEditDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # Prevent editing
        return None

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
    from fstem.lys_instr import MultiMotorDummy
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    dummy = MultiMotorDummy()
    gui = MultiMotorGUI(dummy, 'Multi-Motor Control')
    gui.show()
    sys.exit(app.exec_())