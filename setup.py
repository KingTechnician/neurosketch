from setuptools import setup, find_packages

setup(
    name="neurosketch-utils",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "watchdog>=3.0.0",
    ],
)
