Getting Started
======================================

Simple instrument control template
-----------------------------------------

1. The example code below shows hot to initialize the crystal structure object in lys_mat::

    from lys_mat import Atom, CrystalStructure
    at1 = Atom("Au", (0, 0, 0))
    at2 = Atom("Au", (0.5, 0.5, 0))
    at3 = Atom("Au", (0, 0.5, 0.5))
    at4 = Atom("Au", (0.5, 0, 0.5))
    cell = [4.0773, 4.0773, 4.0773, 90, 90, 90]
    crys = CrystalStructure(cell, [at1, at2, at3, at4])

    print(crys)
    # Symmetry: cubic Fm-3m (No. 225), Point group: m-3m
    # a = 4.07730, b = 4.07730, c = 4.07730, alpha = 90.00000, beta = 90.00000, gamma = 90.00000
    # --- atoms (4) ---
    # 1: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.00000, 0.00000)
    # 2: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.50000, 0.00000)
    # 3: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.50000, 0.50000)
    # 4: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.00000, 0.50000)

2. You can transform the crystal::

    # Primitive cell
    p = crys.createPrimitiveCell()
    print(p)
    # Symmetry: cubic Fm-3m (No. 225), Point group: m-3m
    # a = 2.88309, b = 2.88309, c = 2.88309, alpha = 60.00000, beta = 60.00000, gamma = 60.00000
    # --- atoms (1) ---
    # 1: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.00000, 0.00000)

    # Primitive to conventional
    p = p.createConventionalCell()
    print(p)
    # Symmetry: cubic Fm-3m (No. 225), Point group: m-3m
    # a = 4.07730, b = 4.07730, c = 4.07730, alpha = 90.00000, beta = 90.00000, gamma = 90.00000
    # --- atoms (4) ---
    # 1: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.00000, 0.00000)
    # 2: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.50000, 0.50000)
    # 3: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.00000, 0.50000)
    # 4: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.50000, 0.00000)

    # Supercell
    s = crys.createSupercell([2,1,1])
    print(s)
    # Symmetry: cubic Fm-3m (No. 225), Point group: m-3m
    # a = 8.15460, b = 4.07730, c = 4.07730, alpha = 90.00000, beta = 90.00000, gamma = 90.00000
    # --- atoms (8) ---
    # 1: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.00000, 0.00000)
    # 2: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.00000, 0.00000)
    # 3: Au (Z = 79, Occupancy = 1) Pos = (0.25000, 0.50000, 0.00000)
    # 4: Au (Z = 79, Occupancy = 1) Pos = (0.75000, 0.50000, 0.00000)
    # 5: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.50000, 0.50000)
    # 6: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.50000, 0.50000)
    # 7: Au (Z = 79, Occupancy = 1) Pos = (0.25000, 0.00000, 0.50000)
    # 8: Au (Z = 79, Occupancy = 1) Pos = (0.75000, 0.00000, 0.50000)

    # Deformation
    e = [0.01,0,0,0,0,0] # xx, yy, zz, xy, yz, zx strain
    d = crys.createStrainedCrystal(e)
    print(d)
    # Symmetry: tetragonal I4/mmm (No. 139), Point group: 4/mmm
    # a = 4.11807, b = 4.07730, c = 4.07730, alpha = 90.00000, beta = 90.00000, gamma = 90.00000
    # --- atoms (4) ---
    # 1: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.00000, 0.00000)
    # 2: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.50000, 0.00000)
    # 3: Au (Z = 79, Occupancy = 1) Pos = (0.00000, 0.50000, 0.50000)
    # 4: Au (Z = 79, Occupancy = 1) Pos = (0.50000, 0.00000, 0.50000)

3. You can create parametrized crystal using sympy::

    # Define sympy symbols
    import sympy as sp
    a,b,c = sp.symbols("a,b,c")
    x,y,z = sp.symbols("x,y,z")

    # Create parametrized crystal
    at1 = Atom("H", [x,y,z])
    at2 = Atom("H", [x+0.5,y,z])
    cp = CrystalStructure([a,b,c,90,90,90], [at1, at2])

    print(cp)
    # Failed to find symmetry
    # a = a, b = b, c = c, alpha = 90.00000, beta = 90.00000, gamma = 90.00000
    # --- atoms (2) ---
    # 1: H (Z = 1, Occupancy = 1) Pos = (x, y, z)
    # 2: H (Z = 1, Occupancy = 1) Pos = (x + 0.5, y, z)

    # Substitute parameters
    params = {a:1, b:2, c:3, x: 0, y:0.5, z:0.5}
    cp_subs = cp.subs(params)
    print(cp_subs)
    # Symmetry: orthorhombic Pmmm (No. 47), Point group: mmm
    # a = 1.00000, b = 2.00000, c = 3.00000, alpha = 90.00000, beta = 90.00000, gamma = 90.00000
    # --- atoms (2) ---
    # 1: H (Z = 1, Occupancy = 1) Pos = (0.00000, 0.50000, 0.50000)
    # 2: H (Z = 1, Occupancy = 1) Pos = (0.50000, 0.50000, 0.50000)

4. You can load crystal from standard cif file::

    c = CrystalStructure.loadFrom("cif_file.cif")