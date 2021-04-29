
# use python setup_g2l_v4.py build_ext --inplace
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
#from Pyrex.Distutils import build_ext

setup(
  name = 'g2l_v4',
  # ext_modules=[Extension("g2l_v4",["g2l_v4.pyx"]),],cmdclass={'build_ext': build_ext}
  ext_modules=cythonize([Extension("g2l_v4",["g2l_v4.pyx"]),]),
)
