Installation
============

System Requirements
-------------------

- Python (version >= 3.11).


Install lys_instr from Source
-----------------------------

0. (Only needed if *lys* isn't already installed) Create a Python virtual environment for *lys_instr* (e.g., ``lys_venv``).

   If you use conda:

   .. code-block:: bash

       conda create -n lys_venv python=3.11 pip -y

   If you use venv:

   .. code-block:: bash

       python -m venv lys_venv

1. Activate the created environment or the environment where *lys* is installed:

   Using conda:

   .. code-block:: bash

       conda activate lys_venv

   Using Windows (cmd.exe):

   .. code-block:: bash

       lys_venv\Scripts\activate.bat

   Using Windows (PowerShell):

   .. code-block:: bash

       lys_venv\Scripts\Activate.ps1

   Using Linux / Git Bash:

   .. code-block:: bash
        
       source lys_venv/bin/activate

2. Update pip::

    python -m pip install --upgrade pip

3. Clone *lys_instr* from GitHub::

    git clone https://github.com/zwang154/lys_instr.git

4. Install *lys_instr*:

   .. code-block:: bash

       cd lys_instr
       pip install .

   Or, for development (editable) mode, use:

   .. code-block:: bash

       pip install -e .

5. (Optional but recommended) Create a working directory for *lys_instr* (e.g., ``your_lys_working_dir``)::

    mkdir your_lys_working_dir

6. Choose a working directory and launch *lys* from the activated environment::

    cd your_lys_working_dir
    python -m lys

*lys_instr* is now ready to use within the *lys* platform.