
Switch GUI
==========


Creating a Switch GUI
---------------------

To create a switch GUI subwindow:

1. Launch *lys* and open the ``proc.py`` file (press Ctrl+P).

2. Add the following code to define a class for the switch GUI subwindow and save it (press Ctrl+S).

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import gui, dummy

    class Window(LysSubWindow):
        def __init__(self):
            super().__init__()
            switch = dummy.MultiSwitchDummy("A", "B")   # Create the switch instance
            switchGUI = gui.MultiSwitchGUI(switch)      # Create the switch GUI
            self.setWidget(switchGUI)                   # Embed the switch GUI in the lys subwindow
            self.adjustSize()

Calling ``Window()`` in the *lys* command line launches the GUI subwindow as follows:

.. image:: /lys_instr_/tutorial_/switch_1.png

The dummy switch supports multiple levels: "OFF", "LOW", "MEDIUM", and "HIGH".
Select the desired state for each switch in the list and click **Apply** to enact the change.
The indicator next to each switch shows its connection status—green for connected, red for disconnected or error.

To implement your own switch, subclass ``MultiSwitchInterface`` and implement the required methods, 
similar to the approach described for the :doc:`motor </lys_instr_/tutorial_/motor>`.