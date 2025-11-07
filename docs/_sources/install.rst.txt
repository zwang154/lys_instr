Installation
============

System Requirements
-------------------

- Python (version >= 3.11).


Install lys_instr from Source
-----------------------------

0. (Only needed if *lys* is not already installed) Create a Python virtual environment for *lys_instr* (for example, ``lys_venv``).

   Using conda:

   .. code-block:: bash

       conda create -n lys_venv python=3.11 pip -y

   Using venv:

   .. code-block:: bash

       python -m venv lys_venv

1. Activate the created environment or the environment where *lys* is installed:

   Using conda:

   .. code-block:: bash

       conda activate lys_venv

   Using Windows cmd:

   .. code-block:: bash

       lys_venv\Scripts\activate.bat

   Using Linux / macOS / Git Bash:

   .. code-block:: bash
        
       source lys_venv/bin/activate

2. Update pip::

    pip install --upgrade pip

3. Clone *lys_instr* from GitHub::

    git clone https://github.com/zwang154/lys_instr.git

4. Install *lys_instr* by pip (for installation in the development mode, use ``pip install -e .``)::

    cd lys_instr
    pip install .

5. (Optional but recommended) Create a working directory for *lys_instr* (and *lys*)::

    mkdir your_lys_working_dir

6. Choose a working directory and launch *lys* application from the activated environment by running::

    cd your_lys_working_dir
    python -m lys
