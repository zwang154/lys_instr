import numpy as np
import qtawesome as qta
import os
import ast
import json
from lys.Qt import QtWidgets, QtGui, QtCore


class MultiMotorGUI(QtWidgets.QGroupBox):
    def __init__(self, obj, title):
        super().__init__(title)

        # Set title style (QGroupBox.setAlignment and QGroupBox.setFont do not affect the content)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setFont(QtGui.QFont(self.font().family(), 12))

        self._obj = obj
        self._obj.valueChanged.connect(self._valueChanged)
        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)
        self._obj.valueSet.connect(self._valueSet)
        
        # Load memory file
        dir = os.path.join('.lys_instr', 'GUI', 'MultiMotor')
        os.makedirs(dir, exist_ok=True)
        self._path = os.path.join(dir, 'position_positionList.lst')
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r') as f:
                    txt = f.read()
                    try:
                        self._savedPositions = ast.literal_eval(txt)
                    except Exception:
                        self._savedPositions = []
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, 'File Load Error', f'Could not read file:\n{e}')
                self._savedPositions = []
        else:
            self._savedPositions = []
        
        self._initLayout()

    def _getNamesSettable(self):
        if hasattr(self._obj, 'getNamesSettable'):
            return self._obj.getNamesSettable()
        else:
            return self._obj.getNamesAll()

    def _getNamesjoggable(self):
        if hasattr(self._obj, 'getNamesJoggable'):
            return self._obj.getNamesJoggable()
        else:
            return self._obj.getNamesAll()

    def _initLayout(self):
        self.setStyleSheet('QLineEdit {font-size: 14pt}'
                           'QDoubleSpinBox {font-size: 14pt}'
                           'QPushButton {font-size: 12pt}'
                           'QLabel {font-size: 12pt}')

        # Create main panel
        self._axisNames = {name: QtWidgets.QLabel(name) for name in self._obj.getNamesAll()}
        for lbl in self._axisNames.values():
            lbl.setAlignment(QtCore.Qt.AlignCenter)
        axisNameText = QtWidgets.QLabel('Axis')

        self._nowAt = {name: QtWidgets.QDoubleSpinBox() for name in self._obj.getNamesAll()}
        for dsb in self._nowAt.values():
            dsb.setRange(-np.inf, np.inf)
            dsb.setReadOnly(True)
            dsb.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
            dsb.setDecimals(3)
        nowAtText = QtWidgets.QLabel('Now at')

        self._moveTo = {name: QtWidgets.QLineEdit() for name in self._getNamesSettable()}
        moveToText = QtWidgets.QLabel('Move to')

        jogText = QtWidgets.QLabel('Jog')

        self._jogNega = {name: QtWidgets.QPushButton(qta.icon('ri.arrow-left-fill'), '', clicked=self._nega) for name in self._getNamesjoggable()}
        for btn in self._jogNega.values():
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self._jogNegaReversed = {btn: name for name, btn in self._jogNega.items()}

        self._jogPosi = {name: QtWidgets.QPushButton(qta.icon('ri.arrow-right-fill'), '', clicked=self._posi) for name in self._getNamesjoggable()}
        for btn in self._jogPosi.values():
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self._jogPosiReversed = {btn: name for name, btn in self._jogPosi.items()}

        self._jogStep = {name: QtWidgets.QDoubleSpinBox() for name in self._getNamesjoggable()}
        for dsb in self._jogStep.values():
            dsb.setRange(0, np.inf)
            dsb.setDecimals(2)
        jogStepText = QtWidgets.QLabel('Step')

        self._execute = QtWidgets.QPushButton('Go', clicked=self._setMoveToValue)
        self._execute.setEnabled(True)

        self._interrupt = QtWidgets.QPushButton('Stop', clicked=self._obj.stop)
        self._interrupt.setEnabled(False)

        self._aliveIndicator = {name: QtWidgets.QLabel() for name in self._obj.getNamesAll()}
        for name, lbl in self._aliveIndicator.items():
            alive = self._obj.isAlive()[self._obj._nameList.index(name)]
            icon = qta.icon('ri.checkbox-circle-fill', color='green') if alive else qta.icon('ri.close-circle-fill', color='red')
            lbl.setPixmap(icon.pixmap(24, 24))
            lbl.setAlignment(QtCore.Qt.AlignCenter)

        settings = QtWidgets.QPushButton(qta.icon('ri.settings-5-fill'), '', clicked=self._showSettings)
        settings.setToolTip('Settings')
        settings.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        settings.setIconSize(QtCore.QSize(20, 24))

        self._offset = QtWidgets.QPushButton('Offset', clicked=self._applyOffset)

        self._unsetOffset = QtWidgets.QPushButton('Unset', clicked=self._unsetOffset)
        self._unsetOffset.setEnabled(bool(np.any(self._obj._offsetList)))     # Needs to revist

        # Create collapsible panel
        self._header = QtWidgets.QWidget()

        self._expandButton = QtWidgets.QToolButton()
        # self._expandButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)       # Maybe not needed
        self._expandButton.setArrowType(QtCore.Qt.RightArrow)
        self._expandButton.setCheckable(True)
        self._expandButton.setChecked(False)
        self._expandButton.setAutoRaise(True)
        self._expandButton.setIconSize(QtCore.QSize(14, 14))
        self._expandButton.toggled.connect(self._toggleMemoryTree)

        expanderLine = QtWidgets.QFrame()
        expanderLine.setFrameShape(QtWidgets.QFrame.HLine)
        expanderLine.setStyleSheet('color: lightgray;')

        headerLayout = QtWidgets.QHBoxLayout(self._header)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.addWidget(self._expandButton)
        headerLayout.addWidget(expanderLine)
        headerLayout.setStretch(1, 1)  # Make the line expand to fill the row

        self._memoryPanel = QtWidgets.QWidget()
        memoryPanelText = QtWidgets.QLabel('Memory')

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

        save = QtWidgets.QPushButton('Save', clicked=self._save)
        save.setEnabled(True)
        
        load = QtWidgets.QPushButton('Load', clicked=self._load)
        load.setEnabled(False)

        delete = QtWidgets.QPushButton('Delete', clicked=self._delete)
        delete.setEnabled(False)

        # Main panel layout
        gl = QtWidgets.QGridLayout()
        gl.addWidget(axisNameText, 0, 1)
        gl.addWidget(nowAtText, 0, 2)
        gl.addWidget(moveToText, 0, 3)
        gl.addWidget(jogText, 0, 4)
        gl.addWidget(jogStepText, 0, 6)
        for i, name in enumerate(self._obj.getNamesAll()):
            gl.addWidget(self._aliveIndicator[name], 1 + i, 0, alignment=QtCore.Qt.AlignCenter)
            gl.addWidget(self._axisNames[name], 1 + i, 1)
            gl.addWidget(self._nowAt[name], 1 + i, 2)
            if name in self._getNamesSettable():
                gl.addWidget(self._moveTo[name], 1 + i, 3)
                if name in self._getNamesjoggable():
                    gl.addWidget(self._jogNega[name], 1 + i, 4)
                    gl.addWidget(self._jogPosi[name], 1 + i, 5)
                    gl.addWidget(self._jogStep[name], 1 + i, 6)
        gl.addWidget(self._interrupt, 1 + len(self._nowAt), 2)
        gl.addWidget(self._execute, 1 + len(self._nowAt), 3)
        gl.addWidget(settings, 1 + len(self._nowAt), 0, alignment=QtCore.Qt.AlignCenter)
        gl.addWidget(self._offset, 1 + len(self._nowAt), 4, 1, 2, alignment=QtCore.Qt.AlignCenter)
        gl.addWidget(self._unsetOffset, 1 + len(self._nowAt), 6, alignment=QtCore.Qt.AlignCenter)
        gl.addWidget(self._header, 2 + len(self._nowAt), 0, 1, 7)
        gl.addWidget(self._memoryPanel, 3 + len(self._nowAt), 0, len(self._obj.getNamesAll()), 7)
        self.setLayout(gl)

        # Collapsible panel layout
        buttonGroup = QtWidgets.QHBoxLayout()
        buttonGroup.addWidget(save)
        buttonGroup.addWidget(load)
        buttonGroup.addWidget(delete)

        memoryPanelLayout = QtWidgets.QVBoxLayout(self._memoryPanel)
        memoryPanelLayout.setContentsMargins(0, 0, 0, 0)
        memoryPanelLayout.addWidget(memoryPanelText)
        memoryPanelLayout.addWidget(self._positionList)
        memoryPanelLayout.addLayout(buttonGroup)
        self._memoryPanel.setVisible(False)

        # Show latest saved positions
        self._updateMemory()

    def _setMoveToValue(self):        # Wrapper for self._obj.set(self._moveToValue())
        values = []
        for name in self._moveTo:
            text = self._moveTo[name].text()
            try:
                # values.append(float(text))
                values.append(float(text) + self._obj._offsetList[self._obj._nameList.index(name)])  # Adjust for offset
            except ValueError:
                values.append(np.nan)
        # self._obj.set(values)                                                                    # Pass values as a list
        # self._obj.set({name: value for name, value in zip(self._moveTo.keys(), values)})         # Pass values as a dict
        self._obj.set(**{name: value for name, value in zip(self._moveTo.keys(), values)})       # Pass values as multiple kwargs
        

    def _valueSet(self, valueList):
        for key, value in valueList.items():
            # self._moveTo[key].setText(str(value))
            self._moveTo[key].setText(f'{value - self._obj._offsetList[self._obj._nameList.index(key)]:.3f}')   # Adjust for offset

    def _valueChanged(self, valueList):
        for key, value in valueList.items():
            # self._nowAt[key].setValue(value)
            self._nowAt[key].setValue(value - self._obj._offsetList[self._obj._nameList.index(key)])  # Adjust for offset

    def _busyStateChanged(self, busy):
        anyBusy = bool(any(busy.values()))
        allAlive = all(self._obj.isAlive())
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy and allAlive)
        for btn in self._jogNega.values():
            btn.setEnabled(not anyBusy and allAlive)
        for btn in self._jogPosi.values():
            btn.setEnabled(not anyBusy and allAlive)
        self._execute.setText('Moving' if anyBusy else 'Go')

    def _aliveStateChanged(self, alive):
        busy = self._obj.isBusy()
        anyBusy = bool(busy.any())
        allAlive = alive if isinstance(alive, bool) else all(alive)
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy)
        for name in self._obj.getNamesAll():
            idx = self._obj._nameList.index(name)
            axisAlive = alive if isinstance(alive, bool) else alive[idx]
            if name in self._getNamesjoggable():
                self._jogNega[name].setEnabled(not busy[idx] and axisAlive)
                self._jogPosi[name].setEnabled(not busy[idx] and axisAlive)
            icon = qta.icon('ri.checkbox-circle-fill', color='green') if axisAlive else qta.icon('ri.close-circle-fill', color='red')
            self._aliveIndicator[name].setPixmap(icon.pixmap(24, 24))

    def _nega(self):
        name = self._jogNegaReversed.get(self.sender())
        if name is None:
            return
        self._obj.set({name: self._obj.get(withName=True)[name] - self._jogStep[name].value()})

    def _posi(self):
        name = self._jogPosiReversed.get(self.sender())
        if name is None:
            return
        self._obj.set({name: self._obj.get(withName=True)[name] + self._jogStep[name].value()})

    def _toggleMemoryTree(self, checked):
        self._memoryPanel.setVisible(checked)
        self._expandButton.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
        self.adjustSize()

    def _save(self):
        labels = [item['label'] for item in self._savedPositions]
        i = 1
        while f'{i}' in labels:
            i += 1
        newlabel = f'{i}'
        newPosition = list(self._obj.get())
        newMemo = ''
        self._savedPositions.append({'label': newlabel, 'position': newPosition, 'memo': newMemo})
        try:
            with open(self._path, 'w') as f:
                json.dump(self._savedPositions, f)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Save Error', f'Could not update file:\n{e}')
        self._updateMemory()

    def _load(self):
        selections = self._positionList.selectedItems()
        if not selections:
            return
        try:
            selectedlabel = selections[0].text(0)
            itemDict = next(item for item in self._savedPositions if item['label'] == selectedlabel)
            loadedValues = itemDict['position']
            settableNames = self._getNamesSettable()
            valueDict = {name: loadedValues[self._obj._nameList.index(name)] for name in settableNames}
            self._obj.set(**valueDict)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Load Error', f'Could not load position:\n{e}')

    def _delete(self):
        selectedlabels = {i.text(0) for i in self._positionList.selectedItems()}
        self._savedPositions = [item for item in self._savedPositions if item['label'] not in selectedlabels]
        try:
            with open(self._path, 'w') as f:
                f.write(str(self._savedPositions))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Delete Error', f'Could not update file:\n{e}')
        self._updateMemory()

    def _updateMemory(self):
        self._positionList.clear()      # _positionList is a QTreeWidget
        for itemDict in self._savedPositions:
            label = itemDict['label']
            position = itemDict['position']
            memo = itemDict['memo']
            displayedPosition = ', '.join(f'{v:.3f}' for v in position)
            item = QtWidgets.QTreeWidgetItem([label, displayedPosition, memo])
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)          # Allows editing, but delegates block columns 0 and 1
            self._positionList.addTopLevelItem(item)
        for col in range(self._positionList.columnCount()):
            self._positionList.resizeColumnToContents(col)

    def _memoEdited(self, item, column):
        if column == 2:                             # The memo column
            label = item.text(0)                    # The axis column
            for idx, (n, pos, _) in enumerate(self._savedPositions):
                if n == label:
                    self._savedPositions[idx] = (n, pos, item.text(2))
                    try:
                        with open(self._path, 'w') as f:
                            f.write(str(self._savedPositions))
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(self, 'Memo Edit Error', f'Could not update file:\n{e}')
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

    def _applyOffset(self):
        self._obj.setOffset()
        self._unsetOffset.setEnabled(True)
        for le in self._moveTo.values():
            le.clear()

    def _unsetOffset(self):
        self._obj.clearOffset()
        self._unsetOffset.setEnabled(False)
        for le in self._moveTo.values():
            le.clear()



class NoEditDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):      # Prevents editing of the first two columns
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
        _updateAliveState(): Updates the displayed alive/dead status in the dialog.
    """

    def __init__(self, obj, parent):
        """
        Initializes the settings dialog.

        Args:
            obj (SingleMotorInterface): The motor object whose settings are being managed.
            parent (QWidget): The parent widget for this dialog.
        """
        super().__init__(parent=parent)
        self.setWindowTitle('Settings')
        self._obj = obj
        self._obj.aliveStateChanged.connect(self._updateAliveState)
        self._initLayout()

    def _initLayout(self):
        """
        Creates and initializes all GUI components of the settings dialog, and connects signals to their respective slots.
        """
        self.setStyleSheet('QLineEdit {border-radius: 13px;'
                           'font-size: 15pt;'
                           'border: 0px;'
                           '}')
        
        # Create alive panel
        gl = QtWidgets.QGridLayout()
        self._switch = {name: QtWidgets.QPushButton('Change', clicked=lambda checked, n=name: self._toggleAlive(n)) for name in self._obj.getNamesAll()}
        self._aliveLineEdit = {name: QtWidgets.QLineEdit('Alive') for name in self._obj.getNamesAll()}
        for le in self._aliveLineEdit.values():
            le.setAlignment(QtCore.Qt.AlignCenter)
        for i, name in enumerate(self._obj.getNamesAll()):
            gl.addWidget(self._aliveLineEdit[name], i, 0, alignment=QtCore.Qt.AlignCenter)
            gl.addWidget(self._switch[name], i, 1, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(gl)

        # Show latest alive state
        self._updateAliveState()


    def _toggleAlive(self, name):
        """
        Toggles the alive/dead state of the motor and emits the corresponding signal.
        """
        idx = self._obj._nameList.index(name)
        self._obj._aliveList[idx] = not self._obj.isAlive()[idx]              # Whether OK to call _aliveList()
        # self._obj.aliveStateChanged.emit({name: alive for name, alive in zip(self._obj._nameList, self._obj._aliveList)})
        self._obj.aliveStateChanged.emit(self._obj._aliveList)

    def _updateAliveState(self):
        """
        Updates the displayed alive/dead status in the dialog.
        """
        for name in self._obj.getNamesAll():
            idx = self._obj._nameList.index(name)
            if self._obj.isAlive()[idx]:
                self._aliveLineEdit[name].setText('Alive')
                self._aliveLineEdit[name].setStyleSheet('background-color: #adff2f; color: #000000')
            else:
                self._aliveLineEdit[name].setText('Dead')
                self._aliveLineEdit[name].setStyleSheet('background-color: #ff0000; color: #ffffff')





# To Test the GUI run in the src\python: python -m fstem.lys_instr.GUI.SingleMotorGUI

# if __name__ == '__main__':                                  # Plain MultiMotor
#     import sys
#     from fstem.lys_instr import MultiMotorDummy
#     from lys.Qt import QtWidgets

#     app = QtWidgets.QApplication(sys.argv)
#     dummy = MultiMotorDummy('x', 'y', 'z', 'α', 'β', 'γ')
#     gui = MultiMotorGUI(dummy, 'Multi-Motor Control')
#     gui.show()
#     sys.exit(app.exec_())


# if __name__ == '__main__':                                  # Settable MultiMotor
#     import sys
#     from fstem.lys_instr import MultiMotorDummy, SettableMultiMotor
#     from lys.Qt import QtWidgets

#     app = QtWidgets.QApplication(sys.argv)
#     backend = MultiMotorDummy('x', 'y', 'z', 'α', 'β', 'γ')
#     settable = SettableMultiMotor(backend, axisNamesSettable=['z', 'α', 'y'])
#     gui = MultiMotorGUI(settable, 'Multi-Motor Control')
#     gui.show()
#     sys.exit(app.exec_())


# if __name__ == '__main__':                                  # Joggable MultiMotor
#     import sys
#     from fstem.lys_instr import MultiMotorDummy, JoggableMultiMotor
#     from lys.Qt import QtWidgets

#     app = QtWidgets.QApplication(sys.argv)
#     backend = MultiMotorDummy('x', 'y', 'z', 'α', 'β', 'γ')
#     joggable = JoggableMultiMotor(backend, axisNamesJoggable=['z'])
#     gui = MultiMotorGUI(joggable, 'Multi-Motor Control')
#     gui.show()
#     sys.exit(app.exec_())


# if __name__ == '__main__':                                  # Joggable Settable MultiMotor
#     import sys
#     from fstem.lys_instr import MultiMotorDummy, SettableMultiMotor, JoggableMultiMotor
#     from lys.Qt import QtWidgets

#     app = QtWidgets.QApplication(sys.argv)
#     backend = MultiMotorDummy('x', 'y', 'z', 'α', 'β', 'γ')
#     settable = SettableMultiMotor(backend, axisNamesSettable=['z', 'α', 'y'])
#     joggableSettable = JoggableMultiMotor(settable, axisNamesJoggable=['z'])
#     gui = MultiMotorGUI(joggableSettable, 'Multi-Motor Control')
#     gui.show()
#     sys.exit(app.exec_())


if __name__ == '__main__':                                  # Offsettable Joggable Settable MultiMotor
    import sys
    from fstem.lys_instr import MultiMotorDummy, SettableMultiMotor, JoggableMultiMotor, OffsettableMultiMotor
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    backend = MultiMotorDummy('x', 'y', 'z', 'α', 'β', 'γ')
    settable = SettableMultiMotor(backend, axisNamesSettable=['z', 'α', 'y'])
    joggableSettable = JoggableMultiMotor(settable, axisNamesJoggable=['z'])
    offsettableJoggableSettable = OffsettableMultiMotor(joggableSettable, axisNamesOffsettable=['z'])
    gui = MultiMotorGUI(offsettableJoggableSettable, 'Multi-Motor Control')
    gui.show()
    sys.exit(app.exec_())



# Move whether-to-set to GUI
# Move data conversion in _set() to set()
# Move whether-to-offset to settings
# Keep the interface as simple as possible
# Try to use decorator for a serials of methods
# Use Composition instead of Inheritance whenever possible

# class Motor():
#     def set(x,y):
#         pass

#     def get():
#         pass


# class SettableMotor(Motor):
#     def __init__(self, obj):
#         self._motor = Motor()

#     def set(self, x, y):
#         if "x" in self._obj.getNamesSettable() and "y" in self._obj.getNamesSettable():
#             #super().set(x,y)
#             self._motor.set(x,y)
#         if "x" in self._obj.getNamesSettable() and "y" not in self._obj.getNamesSettable():
#             set(x,self.get()[1])
#         if "x" not in self._obj.getNamesSettable() and "y" in self._obj.getNamesSettable():
#             set(self.get()[0], y)

#     def getNamesSettable(self):
#         return ['x']
