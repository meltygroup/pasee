#!/usr/bin/env python3

"""Setup.py for the Pasee project.
"""

from setuptools import setup, find_packages


def setup_package():
    setup(
        name="pasee",
        version="0.0.1",
        description="HTTP server managing users.",
        long_description="",
        author="Julien Palard",
        author_email="julien@palard.fr",
        license="mit",
        url="https://github.com/meltygroup/pasee",
        classifiers=[
            "Development Status :: 2 - Pre-Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
        ],
        package_dir={"": "src"},
        install_requires=[
            "aiohttp>=3.2.1,<4",
            "coreapi>=2.3.3,<3",
            "cryptography>=2.2.2,<3",
            "pyjwt>=1.6.3,<2",
            "pytoml",
            "shortuuid>=0.5.0",
        ],
        entry_points={"console_scripts": ["pasee = pasee.__main__:main"]},
        extras_require={
            "dev": [
                "flake8",
                "pylint",
                "astroid",
                "pytest-aiohttp",
                "pytest",
                "pytest-cov",
                "aioresponses",
                "detox",
                "bandit",
                "black",
                "mypy",
            ]
        },
        packages=find_packages("src"),
    )


if __name__ == "__main__":
    setup_package()
