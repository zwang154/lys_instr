import os

from lys.Qt import QtWidgets, QtCore
from .Main import fsTEMMain


def initialize(root, dic, generator, layout, scan):
    os.makedirs(".lys/fsTEM", exist_ok=True)
    savepath = ".lys/fsTEM/hardwares.dic"
    if os.path.exists(savepath):
        with open(savepath, mode='r') as f:
            sav = eval(f.read())
    else:
        sav = {}
    dialog = GUIInit(dic, sav)
    result = dialog.exec_()
    if result == QtWidgets.QDialog.Rejected:
        return
    res = dialog.get()
    with open(savepath, mode='w') as f:
        f.write(str(res))
    hardwares = {key: generator(item) for key, item in res.items()}
    gui = fsTEMMain(root, hardwares, layout(), scan())
    return gui


class GUIInit(QtWidgets.QDialog):
    def __init__(self, dic, sav):
        super().__init__()
        self.setStyleSheet("QComboBox {"
                           "border-radius: 4px;"
                           "border:1px solid gray;"
                           "}")
        g = QtWidgets.QFormLayout()
        self._combo = {}
        for key, val in dic.items():
            self._combo[key] = QtWidgets.QComboBox()
            self._combo[key].addItems(val)
            if key in sav:
                self._combo[key].setCurrentText(sav[key])
            g.addRow(key, self._combo[key])

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        vbox1 = QtWidgets.QVBoxLayout()
        vbox1.addLayout(g)
        vbox1.addWidget(btns)
        self.setLayout(vbox1)

    def get(self):
        return {key: c.currentText() for key, c in self._combo.items()}
