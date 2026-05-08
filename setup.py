from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="lake-inspect",
    version="0.1.1",
    description="Health inspector for Iceberg, Delta, and Hudi lakehouse tables",
    long_description=long_description,
    long_description_content_type="text/markdown",
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