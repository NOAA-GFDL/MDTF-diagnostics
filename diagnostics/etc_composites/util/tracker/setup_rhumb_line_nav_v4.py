
# use python setup_rhumb_line_nav_v4.py build_ext --inplace
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
# from Pyrex.Distutils import build_ext

setup(
  name = 'rhumb_line_nav_v4',
  # ext_modules=[Extension("rhumb_line_nav_v4",["rhumb_line_nav_v4.pyx"]),],cmdclass={'build_ext': build_ext}
  ext_modules=cythonize([Extension("rhumb_line_nav_v4",["rhumb_line_nav_v4.pyx"]),]),
)
