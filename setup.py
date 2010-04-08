from setuptools import setup, find_packages

vcs = __import__('vcs')
VERSION = vcs.__version__
readme_file = 'README.rst'
try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "long_description (%s)\n" % readme_file)
    sys.exit(1)

setup(
    name = 'vcs',
    version = VERSION,
    url = 'http://bitbucket.org/marcinkuzminski/vcs/',
    author = 'Marcin Kuzminski, Lukasz Balcerzak',
    author_email = 'marcinkuzminski@gmail.com',
    description = vcs.__doc__,
    long_description = long_description,
    zip_safe = False,
    packages = find_packages(exclude='tests'),
    test_suite = 'nose.collector',
    test_requires = ['nose'],
    install_requires = [
        'nose', 'restkit', 'simplejson', 'mercurial',
    ],
    include_package_data = True,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
)


