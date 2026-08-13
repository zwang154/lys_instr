
lys_instr documentation
=========================

*lys_instr* is a Python package for automating scientific measurements.

It provides reusable interfaces, workflows, and GUI components for coordinating
multiple instruments and assembling custom measurement systems.

.. image:: /lys_instr_/tutorial_/scan_1.png


What can you do with lys_instr?
----------------------------------

The primary use case of *lys_instr* is custom laboratory automation based on
reusable, hardware-independent workflows. Users implement hardware-specific
operations through common controller and detector interfaces, then reuse
workflow and GUI components across instruments and experimental setups. 

This allows measurement environments combining instrument control, workflow
execution, storage, visualization, and graphical interaction to be assembled
with little additional coordination code. Users can therefore focus on
instrument-specific communication and measurement-specific strategies and
algorithms rather than rebuilding the underlying control infrastructure.

A common workflow follows a *control-and-detect* pattern: controllers change
physical or digital parameters, and detectors acquire data. In *lys_instr*,
these operations can be combined into sequential or nested scans.

Key functionalities of *lys_instr*:

- Asynchronous device control and monitoring

- Real-time data visualization and automatic data storage

- Efficient management of nested, multidimensional workflows


Standout features of *lys_instr*:

- Lightweight and efficient: designed to be fast and resource-friendly

- Modular and extensible: easy to reconfigure measurement workflows directly in the GUI

- Seamless integration with `lys <https://github.com/lys-devel/lys>`_ for visualization and analysis


Start with the :doc:`Tutorial </tutorial>` guide for a short walkthrough and practical examples that demonstrate common use cases.


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   install
   tutorial
   api
   contributing

