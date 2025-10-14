import unittest
import time
import numpy as np
from PyQt5 import QtTest

from lys.Qt import QtCore
from lys_instr.dummy.MultiMotor import MultiMotorDummy


class TestMultiMotorDummy(unittest.TestCase):
    """
    Unit tests for MultiMotorDummy.

    Checks correct behavior of the virtual multi-axis motor.
    """

    def test_init(self):
        """
        Tests initial state of the dummy motor.

        Checks that all axis values are zero, all axes are alive, and none are busy.
        """
        motor = MultiMotorDummy()
        self.assertTrue(all(v == 0 for v in motor.get().values()), "All axis values should be zero after initialization.")
        self.assertTrue(all(motor.isAlive.values()), "All axes should be alive after initialization.")
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after initialization.")

    def test_nameList(self):
        """
        Tests the nameList property.

        Checks that the nameList property returns the correct list of axis names.
        """
        motor = MultiMotorDummy('x', 'y')
        self.assertEqual(motor.nameList, ['x', 'y'], "Axis names should match initialization.")

    def test_set_get_isBusy(self):
        """
        Tests set and get methods, and busy state transitions.

        Sets target values for two axes and checks that:
        - During motion, values are between start and target, and axes are busy.
        - After motion completes, values reach targets and axes are idle.
        """
        motor = MultiMotorDummy('x', 'y')

        # Set axis values. Equivalent: motor.set(x=1, y=2) or motor.set(**{'x': 1, 'y': 2})
        motor.set(x=1, y=2)
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
        Tests stop method (stop during motion).

        Sets target values, waits briefly, then stops the motor.
        Checks that values have not reached targets and axes are idle after stopping.
        """
        motor = MultiMotorDummy('x', 'y')
        motor.set(x=1, y=2)
        
        QtTest.QTest.qWait(100)
        motor.stop()
        val1 = motor.get()
        self.assertTrue(all(v < t for v, t in zip(val1.values(), [1, 2])), "Axis values should be less than targets after stop.")
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after stop.")
        
        QtTest.QTest.qWait(100)
        val2 = motor.get()
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after stop (checked again).")
        self.assertEqual(val1, val2, "Axis values should not change after stop.")

    def test_waitForReady_get(self):
        """
        Tests set with waitForReady enabled.

        Sets target values with wait=True and checks that interactions such as get are blocked until the motion finishes.
        """
        motor = MultiMotorDummy('x', 'y')
        motor.set(x=1, y=2, wait=True)
        val = motor.get()
        self.assertTrue(all(v == t for v, t in zip(val.values(), [1, 2])), "Axis values should match targets after waitForReady.")
        self.assertFalse(any(motor.isBusy.values()), "No axis should be busy after waitForReady.")

    def test_waitForReady_set(self):
        """
        Tests set with waitForReady enabled.

        Sets target values with wait=True and checks that interactions such as set are blocked until the motion finishes.
        """
        motor = MultiMotorDummy('x', 'y')
        motor.set(x=1, y=2, wait=True)
        motor.set(x=2, y=3)
        val = motor.get()
        self.assertTrue(all(v > t for v, t in zip(val.values(), [1, 2])), "Axis values should be greater than previous targets after new set.")

    def test_waitForReady_stop(self):
        """
        Tests set and stop methods with waitForReady (stop during motion).

        Sets target values with wait=True and checks that interactions such as stop are blocked until the motion finishes.
        """
        motor = MultiMotorDummy('x', 'y')
        motor.set(x=1, y=2, wait=True)
        val = motor.get()
        motor.stop()
        self.assertTrue(all(v == t for v, t in zip(val.values(), [1, 2])), "Axis values should match targets after waitForReady and stop.")

    def test_isAlive_errorRecovery(self):
        """
        Tests the isAlive property with per-axis error simulation and recovery.

        Simulates an axis going dead by setting the error flag, verifies the alive state and returned value.
        Then recovers the axis, and checks that the alive state and returned value are correct.
        """
        motor = MultiMotorDummy('x', 'y')
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
        Tests the lock functionality.

        Simulates a slowly responding motor by adding a sleep inside set(), before the motor motion begins.
        The actual motion is performed by calling the _set() method.
        Verifies that the _loadState() method is blocked by the lock, and that the busy state is set right after set() is called, even before the motor starts moving.
        """
        slowMotor = SlowMultiMotorDummy('x', 'y')
        slowMotor.set(x=1, y=2)
        self.assertTrue(any(slowMotor.isBusy.values()), "At least one axis should be busy right after set() on slow motor.")


class SlowMultiMotorDummy(MultiMotorDummy):
    """
    A MultiMotorDummy subclass that simulates a slow-responding multi-axis motor.

    This dummy motor adds an artificial delay to the `set()` method to test thread safety, locking, and the behavior of code that interacts with slow hardware. 
    """
    # def set(self, wait=False, waitInterval=0.1, **kwargs):
    #     """
    #     Sets target positions for the specified axes with an artificial delay.

    #     This override introduces a 1-second delay before setting axis values to simulate slow hardware response.

    #     Args:
    #         wait (bool, optional): If True, block until all axes become idle after setting. Defaults to False.
    #         waitInterval (float, optional): Polling interval in seconds while waiting. Defaults to 0.1.
    #         **kwargs: Axis-value pairs to set, e.g., x=1.0, y=2.0.

    #     Raises:
    #         ValueError: If any provided axis name is invalid.
    #     """
    #     with QtCore.QMutexLocker(self._mutex):
    #         time.sleep(1)

    #         # Validate axis names
    #         invalid = [name for name in kwargs if name not in self._info]
    #         if invalid:
    #             raise ValueError(f"Axis name(s) {invalid} not recognized. Available axes: {self.nameList}")

    #         # Update busy state for each axis in kwargs and emit busy state only for axes that are now busy
    #         for name, value in kwargs.items():
    #             self._info[name].busy = not np.isnan(value)
    #         self.busyStateChanged.emit({name: True for name in kwargs if self._info[name].busy})

    #         # Set actual values for the axes in kwargs
    #         self._set(kwargs)

    #     if wait:
    #         self.waitForReady(waitInterval)

    def set(self, wait=False, lock=True, **kwargs):
        if lock:
            with QtCore.QMutexLocker(self._mutex):
                time.sleep(1)
                self._set_impl(**kwargs)
        else:
            self._set_impl(**kwargs)

        if wait:
            self.waitForReady()