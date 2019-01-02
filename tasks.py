#!/usr/bin/env python
# -*- coding: utf-8 -*-

from invoke import task

@task
def clone_pysm(c):
    c.run('mkdir -p libs')
    with c.cd('libs'):
        c.run("git clone git@github.com:pgularski/pysm.git")

@task(clone_pysm)
def copy_pysm_code(c):
    c.run("cp -r libs/pysm/pysm ./")


@task(copy_pysm_code)
def build(c):
    c.run("python setup.py build")


@task(copy_pysm_code)
def sdist(c):
    c.run("python setup.py sdist")
    c.run("python setup.py bdist_wheel")
    c.run("rm dist/*.orig")


@task
def deploy(c):
    c.run("twine upload dist/*")


@task
def clean(c):
    patterns = ['build', 'dist', 'pysm', '__pycache__', 'upysm.egg-info',
            '.eggs', 'libs']
    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))
