Motor Generalization
====================

Generalizing the Motor Concept
------------------------------

A motor may represent a controller for various physical parameters, such as temperature, electric or magnetic field, or other device-specific quantities, 
as long as the underlying control logic is implemented in a subclass inheriting from ``MultiMotorInterface``.

On/off switches can also be represented as motors with discrete states.
For example, a multi-switch GUI and a dummy switch class inheriting from ``MultiMotorInterface`` are provided (see :class:`.gui.MultiSwitch.MultiSwitchGUI` and :class:`.dummy.MultiSwitch.MultiSwitchDummy`).
The GUI for this multi-switch can be launched in the same way as the motor GUI described above.

