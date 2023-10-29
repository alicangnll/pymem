from setuptools import find_packages
from setuptools import setup

setup(
    name="pymem",
    version="0.0.20",
    license="Mozilla Public License 2.0",
    author="Ali Can Gönüllü",
    author_email="alicangonullu@yahoo.com",
    description="PyMem - Memory Acquisition Tool",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/alicangnll/pymem",
    project_urls={"Bug Report": "https://github.com/alicangnll/pymem/issues/new"},
    install_requires=["pywin32"],
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    py_modules=["pymem"],
    classifiers=[
        "License :: OSI Approved :: Mozilla Public License 2.0",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)