
# use python setup_gcd_v4.py build_ext --inplace
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
# from Pyrex.Distutils import build_ext

setup(
  name = 'gcd_v4',
  # ext_modules=[Extension("gcd_v4",["gcd_v4.pyx"]),],cmdclass={'build_ext': build_ext}
  ext_modules=cythonize([Extension("gcd_v4",["gcd_v4.pyx"]),]),
)
