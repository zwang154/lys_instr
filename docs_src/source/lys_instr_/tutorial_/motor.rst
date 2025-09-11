
Motor Control
=============

Creating a Motor Instance
-------------------------

A motor instance can be created by inheriting from the ``MultiMotor.MultiMotorInterface`` class, which provides the core features for a generic multi-axis motor.  
For real motor hardware, users should implement device-specific behaviors—primarily communication with the hardware—by overriding the appropriate methods in their subclass.  
(Refer to the API documentation for ``MultiMotor.MultiMotorInterface`` to see which methods should be customized for real hardware.)


Here, for demonstration purposes, we provide a dummy motor class ``MultiMotorDummy`` that inherits from ``MultiMotor.MultiMotorInterface`` and simulates motor behavior without connecting to real hardware.
A two-axis motor instance with axes named "x" and "y" can be created as follows:

.. code-block:: python

    from lys_instr.dummy.MultiMotor import MultiMotorDummy

    motor = MultiMotorDummy("x", "y")

CUI methods provided by the ``MultiMotorInterface`` class can then be used to control and monitor the motor instance. For example:

.. code-block:: python

    motor.set(x=1, y=2)
    # Or equivalently: positions = {"x": 1, "y": 2}; motor.set(**positions)
    print(motor.get())
    # Initial positions are {"x": 0, "y": 0} by default.
    # Non-zero numbers will be printed, e.g., {'x': 1.6179983504116535e-05, 'y': 1.6179983504116535e-05}, confirming motor motion.


Creating the Motor GUI
----------------------

A GUI for the motor can be created using the ``gui.MultiMotor.MultiMotorGUI`` class by passing the motor instance as an argument.  
Using the dummy motor instance from above, the GUI can created and displayed as follows:

.. code-block:: python

    # Create the motor instance
    from lys_instr.dummy.MultiMotor import MultiMotorDummy

    motor = MultiMotorDummy("x", "y")

    # Create the GUI application
    import sys
    from lys.Qt import QtWidgets
    from lys_instr.gui.MultiMotor import MultiMotorGUI

    app = QtWidgets.QApplication(sys.argv)
    gui = MultiMotorGUI(motor)
    gui.show()
    sys.exit(app.exec_())

Running the above code will open a GUI window similar to the example shown below:

.. image:: /lys_instr_/tutorial_/motor_1.png
    :scale: 80%

Users can input target positions for each axis and click the `Go` button to start the motion, or set step size and use the arrow buttons to jog in each axis.
Clicking the `Settings` button allows configuration value offsets.
Clicking the `Bookmark` button allows managing position bookmarks.
The green indicator shows whether the device is in connection.
Details on configuring the motor GUI can be found in the :doc:`Motor Options </lys_instr_/tutorial_/motorOptions>` of the Advanced section.


Starting the GUI in *lys*
-------------------------

Beside the above standalone method, the motor GUI can also be started from the *lys* application.
After starting *lys*, open the command log window by clicking the "Show" button at the bottom of the main window.
Then, use the command `motor.start_gui()` to launch the motor GUI.

The minimal code to create a motor GUI window in *lys* is as follows:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr.gui.MultiMotor import MultiMotorGUI
    from lys_instr.dummy.MultiMotor import MultiMotorDummy

    class AppWindow(LysSubWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            motor = MultiMotorDummy("x", "y")
            gui = MultiMotorGUI(motor)
            self.setWidget(gui)
            self.adjustSize()


(User can construct GUIs for the motor instances at will in reference to the sample GUIs provided here.)