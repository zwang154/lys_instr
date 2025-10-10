
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

Calling ``Window()`` in the *lys* command line launches the GUI subwindow as shown below:

.. image:: /lys_instr_/tutorial_/motor_1.png

You can input target positions for each axis and click the 'Go' button to start motion, the 'Stop' button to halt motion, or set the step size and use the arrow buttons to jog each axis.

The indicator next to each axis shows its connection status—green for a successful connection, and red for a disconnected or error state.

Clicking the "Settings" button opens a dialog.

.. image:: /lys_instr_/tutorial_/motor_2.png
    :scale: 80%

Within the dialog, you can offset each axis.
Clicking the "Offset" button defines the current value of the axis as zero and records the offset value in the box to the left.
Clicking the "Unset" button removes the offset and restores the true values.
The "Now At" and "Move To" fields in the main window are automatically updated to reflect the current offset.

See also :doc:`Motor Options </lys_instr_/tutorial_/motorOptions>` for details on customizing the motor GUI.