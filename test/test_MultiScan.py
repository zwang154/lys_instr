import unittest
import time
import tempfile
import numpy as np
from pathlib import Path

from PyQt5 import QtTest, QtCore
from lys_instr import MultiScan, ScanAxis, DataStorage, MultiSwitchInterface
from lys_instr.MultiScan import Loop, _Counter
from lys_instr.dummy import MultiMotorDummy, MultiSwitchDummy, MultiDetectorDummy

class TestScanAxis(unittest.TestCase):
    def test_init(self):
        """
        Test that the ScanAxis object is initialized correctly.
        """
        # Test motor
        dummy_motor = MultiMotorDummy("motor")
        values = np.arange(5)
        scan_axis = ScanAxis("motor", dummy_motor, values)
        self.assertEqual(scan_axis.name, "motor", "name should be the same as passed")
        self.assertEqual(scan_axis.obj, dummy_motor, "obj should be the dummy motor")
        np.testing.assert_array_equal(scan_axis.range, values, "range should be the same as passed")

        # Test switch
        dummy_switch = MultiSwitchDummy("switch", levelNames=["A", "B", "C"])
        scan_axis = ScanAxis("switch", dummy_switch, ["A", "B", "C"])
        self.assertEqual(scan_axis.obj, dummy_switch, "obj should be the dummy switch")
        np.testing.assert_array_equal(scan_axis.range, ["A", "B", "C"], "range should be the same as passed")
    
    def test_index_motor(self):
        """
        Test that the index is updated correctly without counter.
        """
        dummy_motor = MultiMotorDummy("test")
        values = np.arange(-1, 1, 0.5)
        scan_axis = ScanAxis("test", dummy_motor, values)
        dummy_motor.set(test=0.0, wait=True)
        self.assertEqual(scan_axis.index, 2, "index should be 2 after setting test to 0.0 without counter")

        counter = _Counter()
        scan_axis.setCounter(counter)
        counter.increment()
        self.assertEqual(scan_axis.index, 0, "index should be 0 after setting counter and first increment")

    def test_index_switch(self):
        """
        Test that the counter is set correctly and index is updated.
        """
        values = ["A", "B", "C"]
        dummy_switch = MultiSwitchDummy("switch", levelNames=values)
        scan_axis = ScanAxis("switch", dummy_switch, values)
        dummy_switch.set(switch="C", wait=True)

        # Test without counter
        self.assertEqual(scan_axis.index, 2, "index should be 2 after setting switch to C without counter")

        # Test with counter
        counter = _Counter()
        scan_axis.setCounter(counter)
        counter.increment()
        self.assertEqual(scan_axis.index, 0, "index should be 0 after setting counter and first increment")        


class TestLoop(unittest.TestCase):
    def test_loop(self):
        """
        Test that the Loop object can be created and used correctly.
        """
        loop = Loop(name="loop")
        for i in range(3):
            loop.set(i)
            self.assertEqual(loop.get()["loop"], i, "loop.set() and loop.get() should work correctly")

class TestMultiScan(unittest.TestCase):
    def _init_storage_detector(self, tmpdir):
        """
        Initialize the storage and detector for the test.
        """
        storage = DataStorage()
        storage.base = tmpdir
        storage.folder = "newFolder"
        storage.name = "newName"

        detector = MultiDetectorDummy()
        storage.connect(detector)
        
        return storage, detector

    def _qWait(self, scan, timeout=5):
        """
        Wait for the scan to finish.
        """
        start = time.time()
        while (scan._busy and (time.time() - start < timeout)):
            QtTest.QTest.qWait(10)

    def test_start_and_finish_signal(self):
        """
        Test that the MultiScan object can be started correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            scanlist = [ScanAxis("scan1", MultiMotorDummy("scan1", speed=100), np.arange(3))]
            scan = MultiScan(storage, scanlist, detector, exposure=0.1)

            finish_emitted = False
            def on_finished():
                nonlocal finish_emitted
                finish_emitted = True
                
            scan.finished.connect(on_finished)
            scan.start()

            self.assertTrue(scan._busy, "Scan should be busy during execution")
            self._qWait(scan)
            self.assertFalse(scan._busy, "Scan should not be busy after completion")
            self.assertTrue(finish_emitted, "Finish signal should be emitted")

            count = len(list(Path(storage.base, storage.folder).glob("*.npz")))
            self.assertEqual(count, 3, "Should have saved all files")
    
    def test_stop(self):
        """
        Test that the MultiScan object can be stopped correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            scanlist = [ScanAxis("scan1", MultiMotorDummy("scan1", speed=100), np.arange(5))]

            scan = MultiScan(storage, scanlist, detector, exposure=0.1)

            stopped_emitted = False
            def on_stopped():
                nonlocal stopped_emitted
                stopped_emitted = True
                
            scan.stopped.connect(on_stopped)

            scan.start()
            time.sleep(0.2)
            scan.stop()
            self._qWait(scan)
            self.assertFalse(scan._busy, "Scan should not be busy after stopping")
            self.assertTrue(stopped_emitted, "Stopped signal should be emitted")

            count = len(list(Path(storage.base, storage.folder).glob("*.npz")))
            self.assertLess(count, 5, "Should have saved less than five files")
    
    def test_move(self):
        """
        Test that the MultiScan object can move the motor correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            motor = MultiMotorDummy("scan1", speed=10)
            values = np.arange(-2.0, 3.0, 0.5)
            scanlist = [ScanAxis("scan1", motor, values)]

            scan = MultiScan(storage, scanlist, detector, exposure=0.05)

            count = -1
            busy = False

            scan.start()
            while count < 3:
                if motor.isBusy["scan1"]:
                    busy = True
                elif busy:
                    busy = False
                    count += 1
                    now = motor.get()["scan1"]
                    self.assertAlmostEqual(now, values[count], delta=0.01, msg="Motor should move to the correct position")
                time.sleep(0.01)

            scan.stop()
            self._qWait(scan)
    
    def test_fileName(self):
        """
        Test that the MultiScan object can save data with correct file names.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            scanlist = [ScanAxis("scan1", MultiMotorDummy("scan1", speed=100), np.arange(0.1, 0.5, 0.1))]

            fileName = "motor_[1]"
            scan = MultiScan(storage, scanlist, detector, exposure=0.01, fileName=fileName)
            scan.start()
            self._qWait(scan)
            
            base = Path(storage.base, storage.folder)
            files = [p.relative_to(base).as_posix() for p in base.rglob("*.npz")]
            self.assertCountEqual(files, ["motor_0.npz", "motor_1.npz", "motor_2.npz", "motor_3.npz"], "Should have saved all files with correct names: [number] should be replaced by the index of the scan")

        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            scanlist = [ScanAxis("scan1", MultiMotorDummy("scan1", speed=100), np.arange(0.1, 0.5, 0.1))]

            fileName = "test/motor_{1}"
            scan = MultiScan(storage, scanlist, detector, exposure=0.01, fileName=fileName)
            scan.start()
            self._qWait(scan)
            
            base = Path(storage.base, storage.folder)
            files = [p.relative_to(base).as_posix() for p in base.rglob("*.npz")]
            self.assertCountEqual(files, ["test/motor_0.1.npz", "test/motor_0.2.npz", "test/motor_0.3.npz", "test/motor_0.4.npz"], "Should have saved all files with correct names: {number} should be replaced by the value of the scan and the folder should be created.")

        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            values = ["A", "B", "C", "D"]
            scanlist = [ScanAxis("switch1", MultiSwitchDummy("switch1", interval=0.01), values)]

            fileName = "switch_{1}/test"
            scan = MultiScan(storage, scanlist, detector, exposure=0.01, fileName=fileName)
            scan.start()
            self._qWait(scan)
            
            base = Path(storage.base, storage.folder)
            files = [p.relative_to(base).as_posix() for p in base.rglob("*.npz")]
            self.assertCountEqual(files, ["switch_A/test.npz", "switch_B/test.npz", "switch_C/test.npz", "switch_D/test.npz"], "Should have saved all files with correct names: It should be possible to use a substituted name as a folder name.")

    def test_hierarchy(self):
        """
        Test that the MultiScan object can save data with correct file names.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            motor = MultiMotorDummy("motor1", "motor2")
            switch = MultiSwitchDummy("switch")
            scanlist = [ScanAxis("motor1", motor, np.arange(3)), ScanAxis("switch", switch, ["A", "B"]), ScanAxis("motor2", motor, np.arange(2))]

            fileName = "motor2_{3}/{2}/motor1_{1}"
            scan = MultiScan(storage, scanlist, detector, exposure=0.01, fileName=fileName)
            scan.start()
            self._qWait(scan)
            
            base = Path(storage.base, storage.folder)
            files = [p.relative_to(base).as_posix() for p in base.rglob("*.npz")]
            self.assertCountEqual(files, ["motor2_0/A/motor1_0.npz", "motor2_0/A/motor1_1.npz", "motor2_0/A/motor1_2.npz",
                                        "motor2_0/B/motor1_0.npz", "motor2_0/B/motor1_1.npz", "motor2_0/B/motor1_2.npz", 
                                        "motor2_1/A/motor1_0.npz", "motor2_1/A/motor1_1.npz", "motor2_1/A/motor1_2.npz", 
                                        "motor2_1/B/motor1_0.npz", "motor2_1/B/motor1_1.npz", "motor2_1/B/motor1_2.npz"], "Should be executed correctly even the scan is a hierarchical structure.")
    
    def test_motor_switch_same_object(self):
        """
        Test that the MultiScan object can save data with correct file names.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            motor = MultiMotorDummy("motor")
            switch = _MultiSwitchDummyForMotorDummy("switch", motor=motor, axis="motor", levelNames=['OFF', 'ON'])
            scanlist = [ScanAxis("switch", switch, ["OFF", "ON"]), ScanAxis("motor", motor, np.arange(3))]

            fileName = "{1}/[2]"
            scan = MultiScan(storage, scanlist, detector, exposure=0.01, fileName=fileName)
            scan.start()
            self._qWait(scan)
            
            base = Path(storage.base, storage.folder)
            files = [p.relative_to(base).as_posix() for p in base.rglob("*.npz")]
            self.assertCountEqual(files, ["OFF/0.npz", "OFF/1.npz", "OFF/2.npz", "ON/0.npz", "ON/1.npz", "ON/2.npz"], "Even when a motor and a switch control the same device, the index must be obtained correctly.")
    
    def test_highspeed_scan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            scan1 = MultiMotorDummy("scan1", speed=1e6)
            scanlist = [ScanAxis("scan1", scan1, np.arange(10))]
            
            fileName = "test_[1]"
            scan = MultiScan(storage, scanlist, detector, exposure=1e-6, fileName=fileName)
            scan.start()
            self._qWait(scan)
            
            base = Path(storage.base, storage.folder)
            files = [p.relative_to(base).as_posix() for p in base.rglob("*.npz")]
            self.assertCountEqual(files, [f"test_{i}.npz" for i in range(10)], "The scan must operate correctly even when motor movement and detector exposure are extremely fast.")

    def test_runs_in_separate_thread(self):
        """
        Test that the scan runs in a separate thread from the main thread.
        """

        def check_thread_id(main, scan):
            self.assertNotEqual(main, scan, "Scan should run in a separate thread from the main thread")

        with tempfile.TemporaryDirectory() as tmpdir:
            storage, detector = self._init_storage_detector(tmpdir)
            motor1 = _ThreadCaptureMotor("motor1", speed=100)
            motor2 = _ThreadCaptureMotor("motor2", speed=100)
            storage.connect(detector)
            scanlist = [ScanAxis("motor1", motor1, np.arange(3)), ScanAxis("motor2", motor2, np.arange(3))]
            scan = MultiScan(storage, scanlist, detector, exposure=0.01)

            main_thread_id = int(QtCore.QThread.currentThreadId())
            motor1.thread_id.connect(lambda scan_thread_id: check_thread_id(main_thread_id, scan_thread_id))
            motor2.thread_id.connect(lambda scan_thread_id: check_thread_id(main_thread_id, scan_thread_id))

            scan.start()
            self._qWait(scan)

class _MultiSwitchDummyForMotorDummy(MultiSwitchInterface):
    def __init__(self, name, motor, axis, levelNames=['OFF', 'ON'], **kwargs):
        super().__init__(levelNames, name, **kwargs)
        self._motor = motor
        self._axis = axis
        self._motor.busyStateChanged.connect(self._on_busy_changed)
        self._state = {name: 'OFF'}
        self.__busy = {name: False}
        self.start()

    def _set(self, **target):
        for name, value in target.items():
            if value == 'ON':
                self._motor.set(**{self._axis: 0}, wait=True)
            self._state[name] = value
    
    def _on_busy_changed(self, dic):
        for busy in dic.values():
            self.__busy[list(self.__busy.keys())[0]] = busy

    def _get(self):
        return self._state

    def _isBusy(self):
        return self.__busy

    def _isAlive(self):
        return {list(self._state.keys())[0]: True}

class _ThreadCaptureMotor(MultiMotorDummy):
    thread_id = QtCore.pyqtSignal(int)
    """
    Custom motor that captures the thread ID during _set operations.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _set(self, **target):
        self.thread_id.emit(int(QtCore.QThread.currentThreadId()))
        super()._set(**target)
