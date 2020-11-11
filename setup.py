from setuptools import setup, find_packages
import os

with open("requirements.txt") as f:
    install_requirements = f.read().splitlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="ximilar-client",
    version="1.20.35",
    description="The Ximilar App and Vize.ai Client.",
    url="https://gitlab.com/ximilar-public/ximilar-vize-api",
    author="Michal Lukac, David Novak and Ximilar.com Team",
    author_email="tech@ximilar.com",
    license="Apache 2.0",
    packages=find_packages(),
    keywords="machine learning, multimedia, json, rest, data",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.4",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    install_requires=install_requirements,
    include_package_data=True,
    zip_safe=False,
    namespace_packages=["ximilar"],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
