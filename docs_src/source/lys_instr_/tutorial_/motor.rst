
Motor Control
=============

Creating a Motor Instance
-------------------------

A motor instance can be created by inheriting from the ``MultiMotorInterface`` class, which provides essential features for a generic multi-axis motor.
For real motor hardware, the user should implement device-specific behaviors—primarily hardware communication—by overriding the relevant methods in the subclass (see :class:`.MultiMotor.MultiMotorInterface`).

For demonstration purposes, a dummy motor class ``MultiMotorDummy`` is provided, which inherits from ``MultiMotorInterface`` and simulates motor behavior without connecting to real hardware.
A dummy motor instance with two axes named "x" and "y" can be created as follows:

.. code-block:: python

    from lys_instr import dummy

    motor = dummy.MultiMotorDummy("x", "y")

CUI methods in the ``MultiMotorInterface`` class can be used to control and monitor the motor instance. For example:

.. code-block:: python

    print(motor.get())      # Default positions: {"x": 0, "y": 0}
    motor.set(x=1, y=2)     # Setting target positions immediately starts motion
    print(motor.get())      # During motion: nonzero values; after motion: {"x": 1, "y": 2}


Creating the Motor GUI
----------------------

A GUI for the motor can be created by passing the motor instance to the ``MultiMotorGUI`` class. 
Continuing from the previous example:

.. code-block:: python

    import sys
    from lys.Qt import QtWidgets
    from lys_instr import gui

    app = QtWidgets.QApplication(sys.argv)
    motorGUI = gui.MultiMotorGUI(motor)
    motorGUI.show()
    sys.exit(app.exec_())

A GUI window like the one below will appear:

.. image:: /lys_instr_/tutorial_/motor_1.png
    :scale: 80%

The user can input target positions for each axis and click the 'Go' button to start motion, click the 'Stop' button to halt motion, or set the step size and use the arrow buttons to jog each axis.
The "Settings" button allows configuration of value offsets, and the "Bookmark" button manages position bookmarks.
The green indicators show the connection status of each axis.
(See also :doc:`Motor Options </lys_instr_/tutorial_/motorOptions>` for details on customizing the motor GUI.)


Starting the GUI in *lys*
-------------------------

The motor GUI can also be launched from within the *lys* application (see :doc:`lys Integration </lys_instr_/tutorial_/lysIntegration>`).
After starting *lys*, open the ``proc.py`` file (press Ctrl+P), add the code below, and save it (press Ctrl+S) to define a class that creates the motor GUI subwindow.

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import gui, dummy

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            motor = dummy.MultiMotorDummy("x", "y")  # Create the motor instance
            motorGUI = gui.MultiMotorGUI(motor)      # Create the motor GUI
            self.setWidget(motorGUI)                 # Set the motor GUI as the content of the lys subwindow
            self.adjustSize()

Calling `AppWindow()` in the *lys* command line launches the GUI subwindow like the one below:

.. image:: /lys_instr_/tutorial_/motor_2.png

Alternatively, the user can create a separate script file, e.g., ``your_script_name.py``, that contains the above class, and import it in the ``proc.py`` file as follows:

.. code-block:: python

    def any_name():
        from path_to_your_script import your_script_name
        return your_script_name.AppWindow()

Calling `any_name()` in the *lys* command line launches the same GUI subwindow.


Generalizing the Motor Concept
------------------------------

A motor may represent a controller for various physical parameters, such as temperature, electric or magnetic field, or other device-specific quantities, 
as long as the underlying control logic is implemented in a subclass inheriting from ``MultiMotorInterface``.
On/off switches can also be represented as motors with discrete states.
For example, a multi-switch GUI and a dummy switch class inheriting from ``MultiMotorInterface`` are provided (see :class:`.gui.MultiSwitch.MultiSwitchGUI` and :class:`.dummy.MultiSwitch.MultiSwitchDummy`).
The GUI for this multi-switch can be launched in the same way as the motor GUI described above.

