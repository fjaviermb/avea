import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="avea",
    version="0.0.1",
    author="Hereath",
    author_email="corentinfarque@gmail.com",
    description="Control an Elgato Avea bulb using python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Hereath/avea",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
          'bluepy',
    ],
)
