from setuptools import setup, find_packages

setup(
    name="mpc-tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "zstandard",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            f"mpc = mpc.cli:main",
        ],
    },
    python_requires=">=3.10",
)