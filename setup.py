from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='pyet',
    version='1.0',
    author='Daniel Palma',
    license="MIT",
    long_description=long_description,
    author_email='danivgy@gmail.com',
    url='https://github.com/danthelion/pyet',
    scripts=['pyet/pyet.py'],
    description='Minimal lyrics display for your Spotify tracks.',
    install_requires=['pyobjc', 'bs4']
)
