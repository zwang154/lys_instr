Installation
============

Requirements
------------

*lys_instr* requires Python 3.11 or later and dependencies:

- ``lys-python >= 0.3.6``
- ``qtawesome >= 1.4.0``

These dependencies are installed automatically when *lys_instr* is installed with ``pip`` (See :ref:`install-from-source` below). 
The ``lys-python`` package provides the Qt-based *lys* platform and installs its scientific and GUI dependencies, including NumPy, SciPy, PyQtGraph, QtPy, and PyQt5. 
Users do not need to install these packages separately.

*lys_instr* does not bundle vendor-specific hardware drivers. 
The included dummy devices and tutorials can be used without additional drivers.

To control real hardware, users must separately install the driver or communication library required by the instrument. 
Device-specific communication is then implemented by subclassing the appropriate *lys_instr* controller or detector interface. 
See :doc:`Getting Started </tutorial>` for implementation examples.


.. _install-from-source:

Install lys_instr from Source
-----------------------------

1. Create a Python virtual environment for *lys_instr* (e.g., ``lys_venv``).

   If you use conda:

   .. code-block:: bash

       conda create -n lys_venv python=3.11 pip -y

   If you use venv:

   .. code-block:: bash

       python -m venv lys_venv

2. Activate the created environment:

   Using conda:

   .. code-block:: bash

       conda activate lys_venv

   Using Windows (cmd.exe):

   .. code-block:: bash

       lys_venv\Scripts\activate.bat

   Using Linux:

   .. code-block:: bash
        
       source lys_venv/bin/activate

3. Update pip::

    python -m pip install --upgrade pip

4. Go to the directory where you want to place the source code, then clone the repository::

    git clone https://github.com/zwang154/lys_instr.git

5. Install *lys_instr*:

   .. code-block:: bash

       cd lys_instr
       pip install .

   Or, for editable mode, use:

   .. code-block:: bash

       pip install -e .


*lys_instr* is now ready to use.
See the :doc:`Getting Started </tutorial>` guide for instructions on launching and using *lys_instr*.
