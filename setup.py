from setuptools import setup
# a workaround for a gross bug: http://bugs.python.org/issue15881#msg170215
try: 
    import multiprocessing
except ImportError: 
    pass
    
setup(
    name="hose",
    version="0.0.1",
#    entry_points="""
#    [console_scripts]
#    hose = hose:main
#    """,
    py_modules=['hose'],
    license = "LGPL",
    description = "unix-pipeline-like stream processing in python",
    long_description="""The goal: pipelien equivalence

Given this pipeline in unix shell:

   foo  | bar  | baz 

we should have this in python:

   foo >> bar >> baz 

Any segment should be easily swappable between the python and shell version.
Command foo should be callable from python. Conversely python function that 
implements a segment should be callable as a command.
""",
    author = "tengu",
    author_email = "karasuyamatengu@gmail.com",
    url = "https://github.com/tengu/py-hose",
    classifiers = [
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Environment :: Console",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities", 
        ],
    # it's optional..
    # install_requires='sh'.split(),

    test_suite='nose.collector',
    tests_require=['nose'],
)
