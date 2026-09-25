from setuptools import setup, find_packages

setup(
    name="shot-tool",
    version="0.1.0",
    description="shot",
    author="XIVthk",
    packages=find_packages(),
    py_modules=["shot"],
    install_requires=[
        "cryptography",
        "zstandard",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "shot = shot:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)