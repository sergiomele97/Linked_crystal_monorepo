from pythonforandroid.recipe import PythonRecipe

class PyBoyRecipe(PythonRecipe):
    version = "2.6.0"
    url = "https://files.pythonhosted.org/packages/source/p/pyboy/pyboy-2.6.0.tar.gz"
    depends = ["setuptools", "numpy"]  # <-- Aquí agregamos numpy
    call_hostpython_via_targetpython = False

recipe = PyBoyRecipe()
