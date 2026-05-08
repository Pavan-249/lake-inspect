from setuptools import setup, find_packages

setup(
    name="lake-inspect",
    version="0.1.0",
    description="Health inspector for Iceberg, Delta, and Hudi lakehouse tables",
    packages=find_packages(),
    install_requires=[
        "rich",
        "deltalake",
        "pyarrow",
    ],
    entry_points={
        "console_scripts": [
            "lake-inspect=lakehouse_lint.__main__:main",
        ],
    },
    python_requires=">=3.8",
)