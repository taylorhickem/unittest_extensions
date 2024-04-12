from setuptools import setup, find_packages


def get_version_from_file():
    with open('VERSION', 'r') as f:
        version = f.read()
        f.close()
    return version


setup(
    name='unittest_extensions',
    version=get_version_from_file(),
    packages=find_packages(),
    description='An extension to the python library unittest to run tests from config file and output results to JSON file.',
    install_requires=open("requirements.txt", "r").read().splitlines(),
    include_package_data=True
)
