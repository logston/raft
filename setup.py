from distutils.cmd import Command
import os
from setuptools import setup, find_packages
import subprocess



class PyTestWatch(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        env = os.environ.copy()
        env['PATH'] += ':' + os.environ['VIRTUAL_ENV']
        env['PYTHONPATH'] = 'src'

        subprocess.run(['ptw'], env=env)


setup(
    packages=find_packages('src'),
    package_dir={'': 'src'},
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    cmdclass={'watch': PyTestWatch},
)

