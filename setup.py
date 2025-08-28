from setuptools import setup, find_packages
import sys
from pathlib import Path
sys.path.append('./lys_instr')
sys.path.append('./test')


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="lys_mat",
    packages=find_packages(exclude=("test*",)),
    version="0.1.0",
    description="Python code for measurement system.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ziqian Wang",
    author_email="zwang154@alumni.jh.edu",
    install_requires=open('requirements.txt').read().splitlines(),
)