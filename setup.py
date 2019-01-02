import codecs
import os
from setuptools import setup
import sdist_upip

HERE = os.path.abspath(os.path.dirname(__file__))

# Get __version__
exec(open('pysm/version.py').read())


def read(*parts):
    # Build an absolute path from *parts* and and return the contents of the
    # resulting file.  Assume UTF-8 encoding.
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


setup(
    name='upysm',
    version=__version__,
    url='https://github.com/pgularski/pysm',
    description='Versatile and flexible Python State Machine library - Micropython Port',
    author='Piotr Gularski',
    author_email='piotr.gularski@gmail.com',
    license='MIT',
    long_description=read('README.md'),
    packages=['pysm'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: MicroPython',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Telecommunications Industry',
        'Natural Language :: English',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
    ],
    install_requires=[
        'micropython-collections.deque',
        'micropython-collections.defaultdict',
        'micropython-logging',
    ],
    keywords='finite state machine automaton fsm hsm pda micropython',
    cmdclass={'sdist': sdist_upip.sdist},
)
