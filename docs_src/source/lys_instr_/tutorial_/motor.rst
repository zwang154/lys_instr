
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


Step-by-Step Demonstration
--------------------------

Here we illustrate step-by-step construction of ``YourMotor`` for a dummy device with axes "x" and "y".

Subclass ``MultiMotorInterface`` to create ``YourMotor``, and attach a simulator instance to each axis to supply position values.
(The ``_ValueInfo`` helper in ``lys_instr.dummy`` provides such a simulator.)
The constructor accepts positional axis names via ``*axisNamesAll``, for example, ``YourMotor("x", "y")``.

.. code-block:: python

    from lys_instr import MultiMotorInterface

    class YourMotor(MultiMotorInterface):

        def __init__(self, *axisNamesAll, **kwargs):
            super().__init__(*axisNamesAll, **kwargs)

            from lys_instr.dummy.MultiMotor import _ValueInfo
            self._simulator = {name: _ValueInfo(10) for name in axisNamesAll}  # motor speed: 10 units/s

            self.start()

Alternatively, you can use a constructor that explicitly accepts two axis name parameters, for example, ``axisName_x`` and ``axisName_y``.

.. code-block:: python

    from lys_instr import MultiMotorInterface

    class YourMotor(MultiMotorInterface):

        def __init__(self, axisName_x, axisName_y, **kwargs):
            super().__init__(axisName_x, axisName_y, **kwargs)

            from lys_instr.dummy.MultiMotor import _ValueInfo
            self._simulator = {axisName_x: _ValueInfo(10), axisName_y: _ValueInfo(10)}  # motor speed: 10 units/s
            
            self.start()

Implement ``_set()`` to assign target positions for specified axes (this starts movement in the simulator).
``_set()`` accepts keyword arguments mapping axis names to numeric targets.

.. code-block:: python

        def _set(self, **target):
            for name, d in self._simulator.items():
                if name in target:
                    d.set(target[name])

Implement ``_get()`` to read the position of each simulator axis and return a dictionary mapping axis names to their current positions.

.. code-block:: python

        def _get(self):
            return {name: d.position for name, d in self._simulator.items()}

Implement ``_stop()`` to halt all axis motion by calling each axis's ``stop()`` method.

.. code-block:: python

        def _stop(self):
            for d in self._simulator.values():
                d.stop()

Implement ``_isBusy()`` to check the simulator and return a dictionary mapping axis names to booleans indicating whether each axis is currently moving.

.. code-block:: python

        def _isBusy(self):
            return {name: d.busy for name, d in self._simulator.items()}

Implement ``_isAlive()`` to check the simulator and return a dictionary mapping axis names to booleans indicating whether each axis is connected and functioning.

.. code-block:: python

        def _isAlive(self):
            return {name: not d.error for name, d in self._simulator.items()}

Optionally, implement ``settingsWidget`` to return a *QWidget* for later use by GUI.
The ``_OptionalPanel`` class in the ``lys_instr.dummy.MultiMotor`` module can readily be used.

.. code-block:: python

        def settingsWidget(self):
            from lys_instr.dummy.MultiMotor import _OptionalPanel
            return _OptionalPanel(self)

The class constructed above is actually the ``MultiMotorDummy`` class provided in the ``lys_instr.dummy`` module.


Checking Operations
-------------------

To verify functionality, instantiate your motor class, for example, ``YourMotor``.
(Import it if defined in a separate module.)

.. code-block:: python

    motor = YourMotor(... your parameters ...)

For demonstration, we use the ``YourMotor`` class defined above with two axes, "x" and "y":

.. code-block:: python

    motor = YourMotor("x", "y")

This is functionally equivalent to instantiating the provided ``MultiMotorDummy`` class:

.. code-block:: python

    from lys_instr import dummy

    motor = dummy.MultiMotorDummy("x", "y")

Now, you can use the ``set()``, ``get()``, ``stop()``, ``isBusy()``, and ``isAlive()`` methods provided by ``MultiMotorInterface`` to confirm that the motor is functioning correctly.
For example:

.. code-block:: python

    motor.set(x=1.0, y=2.0)    # You can also set a single axis: motor.set(x=1.0)
    print(motor.get())         # Returns current positions, e.g. {'x': 0.18, 'y': 0.18}
