
Motor Options
=============

Customizing Set, Jog, and Offset Functions
------------------------------------------

The user can choose to enable the "set", "jog", and "offset" functions for selected axes when instantiating the motor GUI.
For example:

.. code-block:: python

    import sys
    from lys.Qt import QtWidgets
    from lys_instr import gui, dummy

    app = QtWidgets.QApplication(sys.argv)
    motor = dummy.MultiMotorDummy("x", "y", "z")
    motorGUI = gui.MultiMotorGUI(motor, axisNamesSettable=("x", "y"), axisNamesJoggable=("x"), axisNamesOffsettable=("x", "z"))
    motorGUI.show()
    sys.exit(app.exec_())

The resulting GUI window appears as follows:

.. image:: /lys_instr_/tutorial_/motorOptions_1.png
    :scale: 80%

In the "Settings" dialog, only the "x" and "z" axes are shown for offset controls, as specified above:

.. image:: /lys_instr_/tutorial_/motorOptions_2.png
    :scale: 80%

The "Offset" button sets the current position value of the axis to zero and records the offset value in the box to the left.
The "Unset" button removes the offset for the axis and restores its true position value.


Bookmarking Positions
---------------------

Clicking the "Bookmark" button expands the panel to allow managing position bookmarks:

.. image:: /lys_instr_/tutorial_/motorOptions_3.png
    :scale: 80%

The "Save" button adds a bookmark for the current position values of all axes to the list. 
A memo input field allows the user to add a description as needed.
Selecting a bookmark from the list and clicking the "Load" button sets the motor to the saved position.
The "Delete" button removes the selected bookmark from the list.
Note that bookmarks always store the true values of each axis, so the offsetting logic does not affect them.