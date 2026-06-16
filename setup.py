from pathlib import Path
import sys

from setuptools import setup

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdist_upip


def read_version():
    version_file = HERE / 'pysm' / 'version.py'
    if not version_file.exists():
        raise RuntimeError(
            'Missing generated pysm/version.py. Build releases with '
            '`python -m scripts.build_upysm --pysm-version latest` or copy a '
            'selected pysm release into ./pysm first.'
        )

    namespace = {}
    exec(version_file.read_text(encoding='utf-8'), namespace)
    return namespace['__version__']


def read(*parts):
    return (HERE.joinpath(*parts)).read_text(encoding='utf-8')


setup(
    name='upysm',
    version=read_version(),
    url='https://github.com/pgularski/upysm',
    project_urls={
        'Source library': 'https://github.com/pgularski/pysm',
    },
    description='MicroPython distribution package for pysm',
    author='Piotr Gularski',
    author_email='piotr.gularski@gmail.com',
    license='MIT',
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    packages=['pysm'],
    zip_safe=False,
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
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
