from setuptools import setup, find_packages

setup(
    name='bd-hooks',
    version="0.0.2",
    description=(
        'This package allows to extend the core functionality using hooks.'
    ),
    long_description='',
    author='Heorhi Samushyia',
    packages=find_packages(),
    python_requires='>=2.7',
    install_requires=['pluginbase', 'six'],
    zip_safe=False
)