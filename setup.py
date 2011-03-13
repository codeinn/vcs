import os
import sys
from setuptools import setup, find_packages

vcs = __import__('vcs')
readme_file = 'README.rst'

try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "long_description (%s)\n" % readme_file)
    sys.exit(1)

# Nose collector won't complain about not being able to import simplevcs
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.simplevcs.test_settings'

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
    test_suite='tests.collector',
    install_requires=['unittest2', 'Pygments'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
)
