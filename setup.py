import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Lxconverter",
    version="0.0.6",
    author="Thorsten Hapke",
    author_email="thorsten.hapke@sap.com",
    description="Converts TMX files to CSV-files and/or stores to HANA table",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thhapke/tmxconverter",
    keywords = ['tmx'],
    #packages=setuptools.find_packages(),
    packages=["Lxconverter"],
    install_requires=[
        'pandas','pyyaml','hdbcli'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            "Lxconverter = Lxconverter.convert:main"
        ]
    },
    classifiers=[
    	'Programming Language :: Python :: 3.6',
    	'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

