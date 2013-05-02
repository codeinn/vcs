import os
import sys
from setuptools import setup, find_packages, Command

vcs = __import__('vcs')
readme_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
    'README.rst'))

try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "long_description (%s)\n" % readme_file)
    sys.exit(1)

install_requires = ['Pygments', 'mock']
if sys.version_info < (2, 7):
    install_requires.append('unittest2')
tests_require = install_requires + ['dulwich', 'mercurial']

class run_flakes(Command):
    description = 'Runs code against pyflakes'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            import pyflakes.scripts.pyflakes as flakes
        except ImportError:
            print "Audit requires PyFlakes installed in your system."
            sys.exit(-1)

        warns = 0
        # Define top-level directories
        dirs = ['vcs']
        for dir in dirs:
            for root, _, files in os.walk(dir):
                for file in files:
                    if file != '__init__.py' and file.endswith('.py') :
                        warns += flakes.checkPath(os.path.join(root, file))
        if warns > 0:
            sys.stderr.write("ERROR: Finished with total %d warnings.\n" % warns)
            sys.exit(1)
        else:
            print "No problems found in sourcecode."


setup(
    name='vcs',
    version=vcs.get_version(),
    url='https://github.com/codeinn/vcs',
    author='Marcin Kuzminski, Lukasz Balcerzak',
    author_email='marcin@python-works.com',
    description=vcs.__doc__,
    long_description=long_description,
    zip_safe=False,
    packages=find_packages(),
    scripts=[],
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='vcs.tests.collector',
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'vcs = vcs:main',
        ],
    },
    cmdclass={'flakes': run_flakes},
)
