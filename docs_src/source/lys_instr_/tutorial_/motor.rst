
Motor
=====

Creating a Motor Instance
-------------------------

A motor instance is created by subclassing ``MultiMotorInterface``, which provides essential features for a generic multi-axis motor.
For real hardware, you should implement device-specific communication methods in your subclass (see ... for details).

For demonstration, we use the dummy motor ``MultiMotorDummy`` (a subclass of ``MultiMotorInterface``) to simulate motor behavior without connecting to real hardware.
A dummy motor instance with two user-defined axes, here named "x" and "y" as an example, can be created as follows:

.. code-block:: python

    from lys_instr import dummy

    motor = dummy.MultiMotorDummy("x", "y")


Creating the Motor GUI
----------------------

To create the motor GUI subwindow:

1. Launch *lys* and open the ``proc.py`` file (press Ctrl+P).

2. Add the following code to define a class for the motor GUI subwindow and save it (press Ctrl+S).

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import gui, dummy

    class Window(LysSubWindow):
        def __init__(self):
            super().__init__()
            motor = dummy.MultiMotorDummy("x", "y")  # Create the motor instance
            motorGUI = gui.MultiMotorGUI(motor)      # Create the motor GUI
            self.setWidget(motorGUI)                 # Embed the motor GUI in the lys subwindow
            self.adjustSize()

Calling ``Window()`` in the *lys* command line launches the GUI subwindow like the one below:

.. image:: /lys_instr_/tutorial_/motor_1.png

You can input target positions for each axis and click the 'Go' button to start motion, the 'Stop' button to halt motion, or set the step size and use the arrow buttons to jog each axis.

The "Settings" button opens a dialog where you can configure axis value offsets.
The green indicators show the connection status for each axis.

See also :doc:`Motor Options </lys_instr_/tutorial_/motorOptions>` for details on customizing the motor GUI.


