#!/usr/bin/env python
# -*- coding: utf-8 -*-

from invoke import task


@task(help={'pysm_version': 'pysm version to package, or "latest"'})
def build(c, pysm_version='latest'):
    c.run(
        'python -m scripts.build_upysm '
        '--pysm-version {0} --check --smoke'.format(pysm_version)
    )


@task(help={'pysm_version': 'pysm version to package, or "latest"'})
def sdist(c, pysm_version='latest'):
    build(c, pysm_version)


@task
def deploy(c):
    c.run("twine upload dist/*")


@task
def clean(c):
    patterns = ['build', 'dist', 'pysm', '__pycache__', 'upysm.egg-info',
                '.eggs']
    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))
