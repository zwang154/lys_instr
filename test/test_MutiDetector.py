import unittest
import time
import numpy as np

from PyQt5 import QtTest
from lys_instr.dummy.MultiDetector import MultiDetectorDummy


class TestMultiDetectorDummy(unittest.TestCase):

    def test_init(self):
        detector = MultiDetectorDummy()
        self.assertTrue(detector.isAlive, "Detector should be alive after initialization.")
        self.assertFalse(detector.isBusy, "Detector should not be busy after initialization.")

    def test_startAcq_isBusy(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        detector.startAcq()
        self.assertTrue(detector.isBusy, "Detector should be busy after starting acquisition.")

    def test_startAcq_data(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        detector.startAcq()

        timeout = 5  # seconds
        start = time.time()
        while len(detector._data) == 0 and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)
        self.assertGreater(len(detector._data), 0, "No data acquired after starting acquisition.")

    def test_startAcq_over(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        detector._numFrames = np.prod(detector._indexDim)
        detector.startAcq()

        timeout = detector._frameTime * np.prod(detector._indexDim) + 5  # seconds
        start = time.time()
        while len(detector._data) < detector._numFrames and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)
        self.assertFalse(detector.isBusy, "Acquisition did not finish automatically.")

    def test_startAcq_wait(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        detector._numFrames = np.prod(detector._indexDim)
        detector.startAcq(wait=True)
        self.assertFalse(detector.isBusy, "Detector should not be busy after waiting for acquisition to finish.")
        self.assertEqual(len(detector._data), 0, "Acquired data should have been cleared after waiting for acquisition to finish.")

    def test_startAcq_wait_output(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        detector._numFrames = int(np.prod(detector._indexDim))
        data = detector.startAcq(wait=True, output=True)
        self.assertEqual(len(data), detector._numFrames, "Length of acquired data should match number of frames.")
        self.assertTrue(all(value.shape == detector._frameDim for value in data.values()), "All acquired data frames should have the correct shape.")
        self.assertTrue(all((value != 0).any() for value in data.values()), "All acquired data frames should contain non-zero values.")

    def test_stop(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        detector.startAcq()

        timeout = 5  # seconds
        start = time.time()
        while len(detector._data) == 0 and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)

        detector.stop()
        self.assertFalse(detector.isBusy, "Detector should not be busy after stopping acquisition.")

    def test_isAlive(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        self.assertTrue(detector.isAlive)
        detector._error = True
        self.assertFalse(detector.isAlive)

    def test_dataShape(self):
        detector = MultiDetectorDummy(indexDim=(2, 2), frameDim=(3, 3), frameTime=0.1)
        self.assertEqual(detector.dataShape, (2, 2, 3, 3))
