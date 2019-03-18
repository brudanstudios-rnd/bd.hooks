from setuptools import setup, find_packages

setup(
    name='bd-hooks',
    version="0.0.1",
    description='Dsktop application launcher.',
    long_description='',
    author='Heorhi Samushyia',
    packages=find_packages(),
    install_requires=["boto3", "QtAwesome", "metayaml", "pluginbase"],
    zip_safe=False
)