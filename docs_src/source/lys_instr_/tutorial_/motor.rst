
Motor
=====

Creating a Motor Instance
-------------------------

A motor instance is created by subclassing ``MultiMotorInterface``, which provides essential features for a generic multi-axis motor.

For real hardware, you should implement device-specific communication methods in your subclass as follows:

.. code-block:: python

    from lys_instr import MultiMotorInterface

    class YourMotor(MultiMotorInterface):       # Give a name to your subclass, e.g., ``YourMotor``

        def __init__(self, *axisNamesAll, **kwargs):
            super().__init__(*axisNamesAll, **kwargs)
            ... your code to establish connection and initialize the instruments ...
            self.start()

        def _set(self, **target):
            # target (dict): Axis names as keys and target positions as values.
            ... your code to tell the instruments to move to the target positions for specified axes ...

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


Here illustrates a step-by-step construction of `YourMotor` assuming a dummy hardware with two axes, "x" and "y".

.. code-block:: python

    from lys_instr import MultiMotorInterface

    class YourMotor(MultiMotorInterface):

        def __init__(self, axisName_x, axisName_y, **kwargs):
            super().__init__(axisName_x, axisName_y, **kwargs)

            # Code to establish connection and initialize the instruments
            # In this case, we simply call a dummy data simulator
            from lys_instr.dummy.MultiMotor import _ValueInfo
            self._simulator = {axisName_x: _ValueInfo(10), axisName_y: _ValueInfo(10)}  # motor speed = 10 units/s
            
            self.start()

        def _set(self, **target):
            # Code to tell the instruments to move to the target positions for specified axes
            for name, d in self._simulator.items():
                if name in target:
                    d.set(target[name])

        def _get(self):
            # Code to read the current positions of all axes from the instruments
            # Returns a dictionary with axis names as keys and current positions (float) as values
            return {name: d.position for name, d in self._simulator.items()}

        def _stop(self):
            # Code to tell the instruments to stop all axes
            for d in self._simulator.values():
                d.stop()

        def _isBusy(self):
            # Code to check if each axis is moving
            # Returns a dictionary with axis names as keys and busy states (bool) as values (True if busy, False if not)
            return {name: d.busy for name, d in self._simulator.items()}

        def _isAlive(self):
            # Code to check if each axis is connected and functioning
            # Returns a dictionary with axis names as keys and alive states (bool) as values (True if alive, False if not)
            return {name: not d.error for name, d in self._simulator.items()}

The class constructed above is in fact the `MultiMotorDummy` class provided in the ``lys_instr.dummy`` module.


Checking Operations
-------------------

To verify functionality, use your own motor class (for example, ``YourMotor``).

.. code-block:: python

    motor = YourMotor(... your parameters ...)

For demonstration, we use the dummy motor ``MultiMotorDummy`` with two axes, "x" and "y", to simulate motor behavior without real hardware.

.. code-block:: python

    from lys_instr import dummy

    motor = dummy.MultiMotorDummy("x", "y")

You can use the ``set()``, ``get()``, ``stop()``, ``isBusy()``, and ``isAlive()`` methods provided by ``MultiMotorInterface`` to confirm that the motor is functioning correctly.
For example:

.. code-block:: python

    motor.set(x=1.0, y=2.0)    # You can also set a single axis: motor.set(x=1.0)
    print(motor.get())         # Returns current positions, e.g. {'x': 0.18, 'y': 0.18}
