from setuptools import setup, find_packages
from vize import __version__

with open('requirements.txt') as f:
    install_requirements = f.read().splitlines()

setup(name='ximilar-vize-api',
    version=__version__,
    description='The Ximilar VIZE.AI API.',
    url='http://ximilar.com/',
    author='Michal Lukac, David Novak',
    author_email='michallukac@outlook.com',
    license='Apache 2.0',
    packages=find_packages(),
    keywords='machine learning, multimedia, json, rest, data',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Private :: Do Not Upload'
    ],
    install_requires=install_requirements,
    include_package_data=True,
    zip_safe=False,
    namespace_packages=["vize"])
