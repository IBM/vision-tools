from setuptools import setup


with open("pipDescription.md", "r") as fh:
    long_description = fh.read()

setup(
    name="Vision Tools",
    version="0.1.0",
    author="Carl Bender",
    author_email="bcarl@us.ibm.com",
    description="Tools to interface with an IBM Visual Insights server's ReST API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibm/vision-tools",
    package_dir={'': 'lib'},
    packages=[
        "vapi",
        "vapi_cli" ],
    scripts=[ "cli/vision" ],
    install_requires=[
         "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache Version 2",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
