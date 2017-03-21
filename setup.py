from setuptools import setup

setup(
    name='pyet',
    version='1.0',
    author='Daniel Palma',
    license="MIT",
    author_email='danivgy@gmail.com',
    url='https://github.com/danthelion/pyet',
    scripts=['pyet/pyet.py'],
    description='Minimal lyrics display for your Spotify tracks.',
    install_requires=['pyobjc', 'bs4']
)
