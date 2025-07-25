from distutils.core import setup
from Cython.Build import cythonize
import numpy as np
import os 

setup(
    ext_modules=cythonize(os.environ['POD_HOME'] + "/*.pyx"),
    include_dirs=[np.get_include()]
)

