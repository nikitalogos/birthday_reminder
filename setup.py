from setuptools import setup, find_packages

# Minimal setup.py file to install locally to make tests work. Not intended for production use.
setup(
    name='birthday_reminder',
    packages=find_packages(),
    zip_safe=False,
)