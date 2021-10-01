from setuptools import setup, find_packages
import os
import re
import subprocess

with open("requirements.txt") as f:
    install_requirements = f.read().splitlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

version_re = re.compile(r"^v_(\d+\.\d+\.\d+)")


def get_version():
    tag = os.environ.get("CI_COMMIT_TAG")
    if tag != None:
        m = version_re.match(tag)
        if m != None:
            return m.group(1)
    try:
        result = subprocess.run(["git", "describe", "--match", "v_*", "--abbrev=0", "HEAD"], stdout=subprocess.PIPE)
        tag = result.stdout.decode("utf-8").rstrip()
        result = subprocess.run(["git", "rev-parse", "--short=6", "HEAD"], stdout=subprocess.PIPE)
        commitid = result.stdout.decode("utf-8").rstrip()
        m = version_re.match(tag)
        if m != None:
            return m.group(1) + "." + commitid
    except FileNotFoundError:
        pass
    return "1.0.0"


setup(
    name="ximilar-client",
    version=get_version(),
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
