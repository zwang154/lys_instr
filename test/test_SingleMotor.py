import unittest
import time
from lys_instr import SingleMotorDummy


class TestSingleMotorDummy(unittest.TestCase):
    """Test SingleMotorDummy
    
    Checks whether SingleMotorDummy functions correctly as a virtual single-channel motor.
    """

    def test_init(self):
        """Test initial state

        Checks that the initial values are: _delay = 0, _busy = False, _alive = True.

        """
        dummy = SingleMotorDummy()
        self.assertEqual(dummy.get(), 0)
        self.assertFalse(dummy.isBusy())
        self.assertTrue(dummy.isAlive())


    def test_set_get(self):
        """Test set and get methods

        Sets _target to a value (5) with default wait=False, during which the motor is in an accessible state.
        After a short time (0.1 s), which is much less than _duration (1 s), gets the _delay and checks that _delay is between 0 and _target (5) and that the state is busy. 
        After _duration has passed, verifies that _delay has reached the _target (5) and the state is now idle.

        """
        dummy = SingleMotorDummy()
        dummy.set(5)
        time.sleep(0.1)

        val = dummy.get()
        self.assertGreater(val, 0)
        self.assertLess(val, 5)
        self.assertTrue(dummy.isBusy())

        time.sleep(dummy._duration)
        self.assertAlmostEqual(dummy.get(), 5, places=2)
        self.assertFalse(dummy.isBusy())


    def test_set_wait_get(self):
        """Test set (with waitForReady enabled) and get methods

        Sets _target to a value (5) with wait=True, keeping the motor in an inaccessible state until the _target is reached.
        Gets the _delay and checks that it has reached the _target (5) and that the state is now idle. 
        """
        dummy = SingleMotorDummy()
        dummy.set(5, wait=True)

        self.assertAlmostEqual(dummy.get(), 5, places=2)
        self.assertFalse(dummy.isBusy())
        

    def test_set_stop(self):
        """Test set and stop methods (stop during motion)

        Sets _target to a value (5).
        Immediately after getting the _delay and checking that it has not reached the _target (5) and the state is busy, stops the motor.
        Checks that _delay has not reached _target (5) and the state is now idle.
        """
        dummy = SingleMotorDummy()
        dummy.set(5)
        time.sleep(0.1)

        self.assertLess(dummy.get(), 5)
        self.assertTrue(dummy.isBusy())
        dummy.stop()
        time.sleep(0.1)

        self.assertLess(dummy.get(), 5)
        self.assertFalse(dummy.isBusy())


    def test_set_stop_2(self):
        """Test set and stop methods (stop after motion finishs)
        
        Sets _target to a value (5).
        Immediately after the _duration (1 s) passes, gets the _delay and checks that it has reached the _target (5) and the state is idle.
        Then, stops the motor and checks that the _delay remains at the _target (5) and the state remains idle.
        """
        dummy = SingleMotorDummy()
        dummy.set(5)

        time.sleep(0.1 + dummy._duration)
        self.assertAlmostEqual(dummy.get(), 5, places=2)
        self.assertFalse(dummy.isBusy())
        dummy.stop()
        time.sleep(0.1)

        self.assertAlmostEqual(dummy.get(), 5, places=2)
        self.assertFalse(dummy.isBusy())
        

    def test_isAlive(self):
        """Test isAlive method
        
        Sets _alive to False and checks that the motor enters the dead state.
        Then sets _alive back to True and checks that the motor returns to the alive state.
        """
        dummy = SingleMotorDummy()
        dummy._alive = False
        self.assertFalse(dummy.isAlive())
        dummy._alive = True
        self.assertTrue(dummy.isAlive())


    def test_timeoutError(self):
        """Test response to TimeoutError
        
        Temporally overrides the _get method, which is repeatedly called by the background _loadState method, to raise a TimeoutError.
        Checks that this causes the state to become dead.
        Then restores the original _get function and checks that the background _loadState method detects the state as alive again.
        """
        dummy = SingleMotorDummy()

        def raiseTimeout():
            raise TimeoutError()

        originalGet = dummy._get
        dummy._get = raiseTimeout
        time.sleep(0.1)
        self.assertFalse(dummy.isAlive())

        dummy._get = originalGet
        time.sleep(0.1)
        self.assertTrue(dummy.isAlive())


