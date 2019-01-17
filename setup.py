from setuptools import setup, find_packages
from ximilar import __version__

with open('requirements.txt') as f:
    install_requirements = f.read().splitlines()

setup(name='ximilar-client',
    version=__version__,
    description='The Ximilar App and Vize.ai Client.',
    url='http://ximilar.com/',
    author='Michal Lukac, David Novak and Ximilar.com Team',
    author_email='tech@ximilar.com',
    license='Apache 2.0',
    packages=find_packages(),
    keywords='machine learning, multimedia, json, rest, data',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: Artificial Intelligence'
    ],
    install_requires=install_requirements,
    include_package_data=True,
    zip_safe=False,
    namespace_packages=["ximilar"])
