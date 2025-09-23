import numpy as np
import pyqtgraph as pg
from lys_instr.gui import MultiDetectorGUI
from lys.Qt import QtWidgets


class MultiDetectorGUI_Opt(MultiDetectorGUI):
    def createDisplayWidget(self):
        self._indexView = pg.ImageView()
        self._indexView.ui.menuBtn.hide()
        self._indexView.ui.roiBtn.hide()
        self._indexView.setMinimumSize(400, 400)
        self._indexView.ui.histogram.hide()
        self._frameView = pg.ImageView()
        self._frameView.ui.menuBtn.hide()
        self._frameView.ui.roiBtn.hide()
        self._frameView.setMinimumSize(400, 400)
        self._frameView.ui.histogram.hide()

    def createDisplayLayout(self):
        imageLayout = QtWidgets.QHBoxLayout()
        imageLayout.addWidget(self._indexView, stretch=1)
        imageLayout.addWidget(self._frameView, stretch=1)
        return imageLayout

    def _update(self):
        if hasattr(self, "_map"):
            self._indexView.setImage(self._map)

    def _dataAcquired(self, data):
        if not hasattr(self, "_map"):
            self._map = np.zeros(self._obj.indexShape)
            self._indexView.setImage(self._map)

        # Display logic: update image array with new frames
        if data:
            for idx, frame in data.items():
                self._map[idx[-frame.ndim:]] = self._indexDisplay(frame)
            self._frameCount += 1

            # Update frame display every N frames or on last frame
            updateInterval = self._params["interval"]
            if self._frameCount % updateInterval == 0 or self._frameCount == len(data):
                self._frameView.setImage(self._frameDisplay(list(data.values())[-1]))
       
        self._indexView.setImage(self._map)

    def _indexDisplay(self, data):
        return np.mean(data) 
    
    def _frameDisplay(self, frame):
        return frame
    


if __name__ == "__main__":
    import sys
    from lys_instr import gui, dummy

    app = QtWidgets.QApplication(sys.argv)
    detector = dummy.MultiDetectorDummy(indexShape=(8, 8), frameShape=(256, 256), exposure=0.1)
    gui = gui.MultiDetectorGUI_Opt(detector)
    gui.show()
    sys.exit(app.exec_())