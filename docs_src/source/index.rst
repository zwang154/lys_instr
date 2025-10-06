.. lys_instr documentation master file, created by
   sphinx-quickstart on Thu Jun 19 17:37:00 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

lys_instr documentation
=========================

*lys_instr* is a Python package for building flexible GUIs to automate scientific measurements. 

It enables researchers to quickly create custom interfaces for coordinating multiple devices and managing measurement workflows, with minimal coding required.

.. image:: /lys_instr_/tutorial_/scan_1.png

What can you do with *lys_instr*:

Most scientific measurements follow a *move-and-detect* pattern—parameters are adjusted via motors or digital controls (*move*) and data are collected through detectors (*detect*).
A measurement sequence that combines *move* and *detect* is known as a *scan*; complete workflows may involve multiple nested *scans*.
*lys_instr* helps you construct, control, and automate such workflows efficiently.
In principle, you only need to provide minimal code for device-specific communication; the package handles the rest.


Key functionalities of *lys_instr*:

- Asynchronous device control and monitoring

- Real-time data visualization and automatic data storage

- Efficient management of nested workflows


Distinctive features of *lys_instr*:

- Lightweight and efficient: designed to be fast and resource-friendly

- Modular and extensible: easy to reconfigure measurement workflows directly in the GUI

- Seamless integration with data analysis tools: *lys* (https://github.com/lys-devel/lys)


To explore *lys_instr*, please refer to the :doc:`Getting Started </tutorial>` guide and the :doc:`API Reference </api>` for detailed information on classes and methods.

We recommend following the :doc:`Getting Started </tutorial>` guide to become familiar with this package and referring to the examples there for various use cases.


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   install
   tutorial
   api
   contributing

