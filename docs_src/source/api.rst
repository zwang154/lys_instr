
Python API
==========

Package Overview
----------------

The package is organized into hardware interfaces, reusable workflow
components, GUI widgets, and example implementations.

.. list-table:: Package modules
   :header-rows: 1
   :widths: 24 46 30

   * - Module or package
     - Purpose
     - Main public entry points
   * - ``lys_instr.Interfaces``
     - Provides the threaded hardware base class, state monitoring, Qt
       signals, and synchronization used by device interfaces.
     - ``HardwareInterface``
   * - ``lys_instr.MultiController``
     - Defines common interfaces for multi-axis continuous controllers,
       such as motors, and discrete-state controllers, such as switches.
     - ``MultiControllerInterface``, ``MultiMotorInterface``,
       ``MultiSwitchInterface``
   * - ``lys_instr.MultiDetector``
     - Defines the detector acquisition interface, including threaded
       acquisition, detector state, multidimensional data, and axis metadata.
     - ``MultiDetectorInterface``
   * - ``lys_instr.DataStorage``
     - Manages file naming, output directories, and automatic storage of
       acquired data.
     - ``DataStorage``
   * - ``lys_instr.PreCorrection``
     - Describes dependencies between controller axes using functions or
       interpolated calibration data.
     - ``PreCorrector``
   * - ``lys_instr.gui``
     - Provides reusable Qt widgets for controllers, detectors, storage,
       scans, controller memory, and axis dependency.
     - ``MultiMotorGUI``, ``MultiSwitchGUI``, ``MultiDetectorGUI``,
       ``DataStorageGUI``, ``ScanWidget``, ``ControllerMemory``,
       ``PreCorrectorGUI``
   * - ``lys_instr.dummy``
     - Provides simulated devices for tutorials, development, and testing
       without physical hardware.
     - ``MultiMotorDummy``, ``MultiSwitchDummy``,
       ``MultiDetectorDummy``
   * - ``lys_instr.templates``
     - Provides examples of complete measurement windows assembled from
       dummy devices, storage, scan logic, and GUI components.
     - ``Window`` and ``TemplateWindow`` examples
   * - ``lys_instr.Utilities``
     - Provides a timing utility used internally by the interfaces.
     - ``preciseSleep``

The principal device classes can be imported directly from ``lys_instr``.
GUI classes and dummy devices are available from their respective
subpackages:

.. code-block:: python

    from lys_instr import MultiMotorInterface, MultiDetectorInterface
    from lys_instr.gui import MultiMotorGUI, MultiDetectorGUI
    from lys_instr.dummy import MultiMotorDummy, MultiDetectorDummy


Core Elements
-------------
.. toctree::
   :maxdepth: 1

   lys_instr_/api_/base
   lys_instr_/api_/motor
   lys_instr_/api_/detector
   lys_instr_/api_/storage
   lys_instr_/api_/extensions

Utilities
---------
.. toctree::
   :maxdepth: 1

   lys_instr_/api_/utilities

Combinations
------------
.. toctree::
   :maxdepth: 1

   lys_instr_/api_/scan

Dummy Devices
-------------
.. toctree::
   :maxdepth: 1

   lys_instr_/api_/dummyMotor
   lys_instr_/api_/dummyDetector
