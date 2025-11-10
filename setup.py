from setuptools import setup, find_packages
import sys
from pathlib import Path
sys.path.append('./lys_instr')
sys.path.append('./test')


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="lys_instr",
    packages=find_packages(exclude=("test*",)),
    version="0.1.0",
    description="A Python package for automating scientific measurements.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ziqian Wang",
    author_email="zwang154@alumni.jh.edu",
    install_requires=open('requirements.txt').read().splitlines(),
    include_package_data=True,
    package_data={'lys_instr': ['resources/*']},
)