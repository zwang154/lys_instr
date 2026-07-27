:tocdepth: 1

Testing
=======

Testing in *lys_instr* follows the same separation as the package design: automated tests check core, non-GUI interface behavior, while manual checks verify GUI components and combined GUI-based workflows.


Automated Tests (Non-GUI Behavior)
----------------------------------

Using the dummy devices included with the package, the automated tests verify that the Base Layer interfaces and other core non-GUI components behave as expected.
They can also be used as references when writing pytest files for user-defined device subclasses.

Before running the tests, ensure *lys_instr* is installed from source (see :doc:`/install`).

Install ``pytest`` and ``pytest-cov`` if they are not already installed::

    pip install pytest pytest-cov

Go to the *lys_instr* source directory and run the tests::

    python -m pytest

To check code coverage, run::

    python -m pytest --cov=lys_instr


Manual Checks (GUI Components and Workflows)
--------------------------------------------

Manual GUI checks complement the automated tests by verifying behavior that depends on interactive Qt widgets and user operations.
The tutorial pages provide exemplary screenshots for each GUI component; key operations to check are summarized below.
You can replace the dummy devices with your own implementations for real hardware checks as necessary.

Start *lys* from the source or working directory::

    python -m lys

Then follow the corresponding tutorial page to launch the component and perform the checks below.


Motor GUI
~~~~~~~~~

See :doc:`/lys_instr_/tutorial_/motorGUI`. Check that:

- The window opens without errors.

- Motor axes and current positions are displayed and updated.

- Entering target values and clicking **Go** starts motion.

- Clicking **Stop** interrupts ongoing motion.

- Jog, offset, settings, and bookmark controls behave as expected when enabled.

- Alive indicators and control availability reflect each axis's alive and busy states.


Switch GUI
~~~~~~~~~~

See :doc:`/lys_instr_/tutorial_/switchGUI`. Check that:

- The window opens without errors.

- Switch states are displayed for each axis.

- Selecting a state and clicking **Apply** updates the switch.

- Alive indicators and control availability reflect each axis's alive and busy states.


Detector GUI
~~~~~~~~~~~~

See :doc:`/lys_instr_/tutorial_/detectorGUI`. Check that:

- The window opens without errors.

- Exposure and acquisition settings can be changed.

- Clicking **Acquire** starts a single acquisition.

- Clicking **Stream** starts repeated or continuous acquisition.

- Clicking **Stop** stops acquisition.

- Acquired data are displayed and updated in the viewer.

- The alive indicator and acquisition-button states reflect the detector's alive and busy states.


Storage GUI
~~~~~~~~~~~

See :doc:`/lys_instr_/tutorial_/storageGUI`. Check that:

- The window opens without errors.

- The base folder, folder name, and file name fields can be changed.

- The **Enabled** and **Numbered** options update the storage behavior.

- When storage is connected to a detector, acquired data are saved to the selected path.

- The saving status updates during and after file writing.


Scan GUI
~~~~~~~~

See :doc:`/lys_instr_/tutorial_/scanGUI`. Check that:

- The window opens without errors.

- Motor and switch scan rows can be added and configured.

- A scan can be started and stopped.

- During a scan, motor values, detector acquisition, and storage updates proceed in the expected order.


Axis Dependency GUI
~~~~~~~~~~~~~~~~~~~

See :doc:`/lys_instr_/tutorial_/preCorrection`. Check that:

- The window opens without errors.

- Target and variable axes can be added and configured.

- Entering an expression such as ``x/2`` for target ``y`` creates the expected correction.

- Moving the variable axis updates the target axis according to the correction.

- Data-based corrections can be imported from a NumPy ``.npz`` file and applied.

- Selecting **Enable/Disable** from a target's context menu controls whether the correction is applied.
