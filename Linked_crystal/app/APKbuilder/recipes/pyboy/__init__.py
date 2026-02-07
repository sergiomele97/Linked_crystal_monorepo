from pythonforandroid.recipe import PythonRecipe

class PyBoyRecipe(PythonRecipe):
    version = "2.6.0"
    url = "https://github.com/pyboy-for-android/PyBoy/archive/refs/heads/android-2.6.0.zip"
    depends = ["setuptools", "numpy"]
    call_hostpython_via_targetpython = False

recipe = PyBoyRecipe()
