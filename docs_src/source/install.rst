Installation
=============================

System Requirements
-------------------------

- Python (version >= 3.11).


Install lys
-----------

Refer to the `lys installation guide <https://lys-devel.github.io/lys/install.html>`_ for instructions on installing *lys*.


Install lys_instr from Source
-------------------------------

1. Activate the Python environment where *lys* is installed (for example, ``lys_venv``)::

    # When using conda:
    conda activate lys_venv

    # When using virtualenv:
    source lys_venv/bin/activate

    # In cmd:
    lys_venv\Scripts\activate.bat

2. Update pip inside the environment (``lys_venv``)::

    python -m pip install --upgrade pip

3. Clone *lys_instr* from GitHub::

    git clone https://github.com/zwang154/lys_instr.git


4. Install *lys_instr* by pip. If you want to install *lys_instr* in development mode, add `-e` option after `pip install`::

    cd lys_instr
    pip install .

5. Choose a working directory and launch *lys* from the activated environment by running::

    python -m lys

Note that the current directory of the system is used as the working directory of *lys_instr*.


