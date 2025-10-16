import unittest
import time
from PyQt5 import QtTest
from lys_instr.dummy.MultiSwitch import MultiSwitchDummy

class TestMultiSwitchDummy(unittest.TestCase):
    def test_init(self):
        switch = MultiSwitchDummy('A', 'B')
        self.assertEqual(switch.nameList, ['A', 'B'])
        self.assertTrue(all(switch.isAlive.values()), "All switches should be alive after initialization.")
        self.assertFalse(any(switch.isBusy.values()), "No switch should be busy after initialization.")

    def test_set_get(self):
        switch = MultiSwitchDummy('A', 'B', levelNames=['OFF', 'ON'])
        switch.set(A='ON', B='OFF')
        # Wait for state to update
        timeout = 1
        start = time.time()
        while any(switch.isBusy.values()) and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)
        state = switch.get()
        self.assertEqual(state['A'], 'ON')
        self.assertEqual(state['B'], 'OFF')

    def test_isBusy(self):
        switch = MultiSwitchDummy('A', 'B', levelNames=['OFF', 'ON'])
        switch.set(A='ON')
        self.assertTrue(switch.isBusy['A'], "Switch A should be busy right after set.")
        # Wait for A to finish
        timeout = 1
        start = time.time()
        while switch.isBusy['A'] and (time.time() - start < timeout):
            QtTest.QTest.qWait(10)
        self.assertFalse(switch.isBusy['A'], "Switch A should not be busy after state change.")

    def test_isAlive_errorRecovery(self):
        switch = MultiSwitchDummy('A', 'B', levelNames=['OFF', 'ON'])
        # Simulate error on A
        switch._data['A'].error = True
        self.assertFalse(switch.isAlive['A'], "Switch A should be dead after error injection.")
        # Recover
        switch._data['A'].error = False
        self.assertTrue(switch.isAlive['A'], "Switch A should be alive after error recovery.")

    def test_settingsWidget(self):
        switch = MultiSwitchDummy('A', 'B')
        widget = switch.settingsWidget()
        self.assertIsNotNone(widget, "Settings widget should be created.")
