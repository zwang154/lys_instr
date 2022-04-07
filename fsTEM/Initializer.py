import os

from PyQt5.QtWidgets import QDialog, QGridLayout, QComboBox, QLabel, QDialogButtonBox, QVBoxLayout
from PyQt5.QtCore import Qt
from lys import home

from .Main import fsTEMMain


def initialize(dic, generator, layout):
    os.makedirs(".lys/fsTEM", exist_ok=True)
    savepath = ".lys/fsTEM/hardwares.dic"
    if os.path.exists(savepath):
        with open(savepath, mode='r') as f:
            sav = eval(f.read())
    else:
        sav = {}
    dialog = GUIInit(dic, sav)
    result = dialog.exec_()
    if result == QDialog.Rejected:
        return
    res = dialog.get()
    with open(savepath, mode='w') as f:
        f.write(str(res))
    hardwares = {key: generator(item) for key, item in res.items()}
    print(hardwares)
    return fsTEMMain(hardwares, layout())


class GUIInit(QDialog):
    def __init__(self, dic, sav):
        super().__init__()

        g = QGridLayout()
        self._combo = {}
        i = 0
        for key, val in dic.items():
            self._combo[key] = QComboBox()
            self._combo[key].addItems(val)
            if key in sav:
                self._combo[key].setCurrentText(sav[key])
            if i % 2 == 0:
                g.addWidget(QLabel(key), 2*int(i/2), 0)
                g.addWidget(self._combo[key], 2*int(i/2) + 1, 0)
            else:
                g.addWidget(QLabel(key), 2*int(i/2), 1)
                g.addWidget(self._combo[key], 2*int(i/2) + 1, 1)
            i += 1

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        vbox1 = QVBoxLayout()
        vbox1.addLayout(g)
        vbox1.addWidget(btns)
        self.setLayout(vbox1)

    def get(self):
        return {key: c.currentText() for key, c in self._combo.items()}
