import unittest
import time
import math
from PyQt5 import QtTest

from lys.Qt import QtCore
from lys_instr.dummy.MultiMotor import MultiMotorDummy


class TestMultiMotorDummy(unittest.TestCase):

    def test_init(self):
        """
        Test that the MultiMotorDummy object is initialized correctly.
        """
        motor = MultiMotorDummy()
        self.assertTrue(all(v == 0 for v in motor.get().values()), "All axis values should be zero after initialization.")
        self.assertTrue(all(motor.isAlive.values()), "All axes should be alive after initialization.")
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after initialization.")

    def test_nameList(self):
        """
        Test that the nameList property returns the correct axis names.
        """
        motor = MultiMotorDummy('x', 'y')
        self.assertEqual(motor.nameList, ['x', 'y'], "Axis names should match initialization.")

    def test_set_get_isBusy(self):
        """
        Test that the set, get, and isBusy properties work correctly.
        """
        motor = MultiMotorDummy('x', 'y', interval=0.01)

        # Set axis values. Equivalent: motor.set(x=1, y=2) or motor.set(**{'x': 1, 'y': 2})
        motor.set(x=1, y=2)
        time.sleep(0.02)
        val = motor.get()
        self.assertTrue(all(0 < v < t for v, t in zip(val.values(), [1, 2])), "Axis values should be between start and target during motion.")
        self.assertTrue(all(motor.isBusy.values()), "All axes should be busy during motion.")
        
        # Wait for x to finish
        timeout = 1/motor._data["x"]._speed + 5    # seconds
        start = time.time()
        while motor.isBusy['x'] and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)
        self.assertEqual([motor.isBusy['x'], motor.isBusy['y']], [False, True], "After x reaches target, x should not be busy, y should still be busy.")

        # Wait for y to finish
        timeout = (2 - 1)/motor._data["y"]._speed + 5    # seconds
        start = time.time()
        while motor.isBusy['y'] and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)
        self.assertEqual([motor.isBusy['x'], motor.isBusy['y']], [False, False], "After both reach target, neither should be busy.")

        val = motor.get()
        self.assertTrue(all(v == t for v, t in zip(val.values(), [1, 2])), "Axis values should match targets after both axes reach their targets.")

    def test_stop(self):
        """
        Test that the stop method works correctly.
        """
        motor = MultiMotorDummy('x', 'y', interval=0.01)
        motor.set(x=1, y=2)
        QtTest.QTest.qWait(1)
        motor.stop()
        time.sleep(0.01)
        val1 = motor.get()
        self.assertTrue(all(v < t for v, t in zip(val1.values(), [1, 2])), "Axis values should be less than targets after stop.")
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after stop.")
        
        QtTest.QTest.qWait(100)
        val2 = motor.get()
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after stop (checked again).")
        self.assertEqual(val1, val2, "Axis values should not change after stop.")

    def test_waitForReady_get(self):
        """
        Test that the waitForReady method works correctly with get.
        """
        motor = MultiMotorDummy('x', 'y')
        motor.set(x=1, y=2, wait=True)
        val = motor.get()
        self.assertTrue(all(v == t for v, t in zip(val.values(), [1, 2])), "Axis values should match targets after waitForReady.")
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after waitForReady.")
        # check that waitForReady did not take too long

    def test_waitForReady_set(self):
        """
        Test that the waitForReady method works correctly with set.
        """
        motor = MultiMotorDummy('x', 'y', interval=0.01)
        motor.set(x=1, y=2, wait=True)
        motor.set(x=2, y=3)
        time.sleep(0.01)
        val = motor.get()
        self.assertTrue(all(v > t for v, t in zip(val.values(), [1, 2])), "Axis values should be greater than previous targets after new set.")

    def test_waitForReady_stop(self):
        """
        Test that the waitForReady method works correctly with stop.
        """
        motor = MultiMotorDummy('x', 'y')
        motor.set(x=1, y=2, wait=True)
        val = motor.get()
        motor.stop()
        self.assertTrue(all(v == t for v, t in zip(val.values(), [1, 2])), "Axis values should match targets after waitForReady and stop.")

    def test_isAlive_errorRecovery(self):
        """
        Test that the isAlive method works correctly with error recovery.
        """
        motor = MultiMotorDummy('x', 'y', interval=0.01)
        motor.set(x=1, y=2)
        QtTest.QTest.qWait(100)

        # Error injection
        motor._data['x'].error = True
        self.assertEqual([motor.isAlive['x'], motor.isAlive['y']], [False, True], "Axis x should be dead, y should be alive after error injection.")

        # Error recovery
        motor._data['x'].error = False
        self.assertEqual([motor.isAlive['x'], motor.isAlive['y']], [True, True], "Both axes should be alive after error recovery.")
        
        # Wait for both axes to reach targets after recovery
        timeout = 2/max(motor._data['x']._speed, motor._data['y']._speed) + 5    # seconds
        start = time.time()
        while (motor.isBusy['x'] or motor.isBusy['y']) and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)

        val = motor.get()
        self.assertTrue(all(v == t for v, t in zip(val.values(), [1, 2])), "Axis values should match targets after recovery and motion.")


    def test_lock(self):
        """
        Test that motor axes report `isBusy` correctly during asynchronous movement using `SlowMultiMotorDummy`.
        """
        slowMotor = SlowMultiMotorDummy('x', 'y')
        slowMotor.set(x=1, y=2)
        self.assertTrue(any(slowMotor.isBusy.values()), "At least one axis should be busy right after set() on slow motor.")

    def test_get_force(self):
        """
        Test that the get method works correctly with force parameter.
        """
        motor = MultiMotorDummy('x', 'y', interval=0.01)
        ini = motor.get()
        motor._set(x=1, y=2, immediate=True)
        self.assertTrue(all(math.isclose(i, v, abs_tol=1e-3) for i, v in zip(ini.values(), motor.get().values())), "get() should return the original value if the value has been manually changed.")
        val = motor.get(force=True)
        self.assertFalse(all(math.isclose(i, v, abs_tol=1e-3) for i, v in zip(ini.values(), val.values())), "get(force=True) should return the current value, which should be different from the original value.")
        self.assertTrue(all(math.isclose(v, v2, abs_tol=1e-3) for v, v2 in zip(val.values(), motor.get().values())), "get() should return the same value that get(force=True) previously returned.")


class SlowMultiMotorDummy(MultiMotorDummy):

    def set(self, wait=False, lock=True, **kwargs):
        if lock:
            with QtCore.QMutexLocker(self._mutex):
                time.sleep(1)
                self._set_impl(**kwargs)
        else:
            self._set_impl(**kwargs)

        if wait:
            self.waitForReady()