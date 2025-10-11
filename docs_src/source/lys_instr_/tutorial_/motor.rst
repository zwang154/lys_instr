
Motor
=====

Creating a Motor Instance
-------------------------

A motor instance is created by subclassing ``MultiMotorInterface``, which provides essential features for a generic multi-axis motor.

For real hardware, you should implement device-specific communication methods in your subclass as follows.

.. code-block:: python

    class YourMotor(MultiMotorInterface):       # Give a name to your subclass, e.g., ``YourMotor``

        def __init__(self, *axisNamesAll, **kwargs):
            super().__init__(*axisNamesAll, **kwargs)
            self.start()

        def _set(self, **target):
            # target (dict): Axis names as keys and target positions as values.
            ... your code to tell the instruments to move to the target positions ...

        def _get(self):
            ... your code to read the current positions of all axes from the instruments ...
            return ... a dictionary with axis names as keys and current positions (float) as values ...

        def _stop(self):
            ... your code to tell the instruments to stop all axes ...

        def _isBusy(self):
            ... your code to check if each axis is moving ...
            return ... a dictionary with axis names as keys and busy states (bool) as values (True if busy, False if not) ...

        def _isAlive(self):
            ... your code to check if each axis is connected and functioning ...
            return ... a dictionary with axis names as keys and alive states (bool) as values (True if alive, False if not) ...


Function Check
--------------

To verify functionality, you should use your own motor class (e.g., ``YourMotor``).

For demonstration, we use the dummy motor ``MultiMotorDummy`` with two axes, "x" and "y", to simulate motor behavior without real hardware.

.. code-block:: python

    from lys_instr import dummy

    motor = dummy.MultiMotorDummy("x", "y")

You can use the ``set()``, ``get()``, ``stop()``, ``isBusy()``, and ``isAlive()`` methods provided by ``MultiMotorInterface`` to verify that the motor operates correctly.
For example:

.. code-block:: python

    motor.set(x=1.0, y=2.0)    # You can also set a single axis: motor.set(x=1.0)
    print(motor.get())         # Returns current positions, e.g. {'x': 0.18, 'y': 0.18}
