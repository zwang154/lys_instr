import setuptools
from setuptools import setup
import sys
sys.path.append('./fsTEM')
sys.path.append('./test')

setup(
    name="fsTEM",
    version="0.2.2",
    packages = setuptools.find_packages()
)
