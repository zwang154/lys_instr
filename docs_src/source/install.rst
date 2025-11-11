Installation
============

System Requirements
-------------------

- Python (version >= 3.11).


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

4. Change to the folder where you want to store the project and then clone the repository::

    git clone https://github.com/zwang154/lys_instr.git

5. Install *lys_instr*:

   .. code-block:: bash

       cd lys_instr
       pip install .

   Or, for editable mode, use:

   .. code-block:: bash

       pip install -e .

6. Go to the directory you want to use as your workspace and then launch *lys*::

    python -m lys

*lys_instr* is now ready to use within the *lys* platform.