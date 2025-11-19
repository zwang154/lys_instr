
lys_instr documentation
=========================

*lys_instr* is a Python package for automating scientific measurements.

It enables users to efficiently create custom GUIs for coordinating multiple instruments and managing measurement workflows with minimal coding required.

.. image:: /lys_instr_/tutorial_/scan_1.png


What can you do with lys_instr?
----------------------------------

Most scientific measurements follow a *control-and-detect* pattern—parameters are changed via physical or digital controls (the *control* step) and data are recorded by detectors (the *detect* step).
A measurement sequence that combines *control* and *detect* is called a *scan*; a complete workflow may consist of nested *scans*.
*lys_instr* helps you construct, control, and automate such workflows efficiently.
In principle, you only need to provide minimal code for device-specific communication—the package handles the rest.


Key functionalities of *lys_instr*:

- Asynchronous device control and monitoring

- Real-time data visualization and automatic data storage

- Efficient management of nested, multi-dimensional workflows


Standout features of *lys_instr*:

- Lightweight and efficient: designed to be fast and resource-friendly

- Modular and extensible: easy to reconfigure measurement workflows directly in the GUI

- Seamless integration with `lys <https://github.com/lys-devel/lys>`_ for analysis and visualization


Start with the :doc:`Tutorial </tutorial>` guide for a short walkthrough and practical examples that demonstrate common use cases.


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   install
   tutorial
   api
   contributing

