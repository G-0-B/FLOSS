#!/usr/bin/env python3
"""
Setup script for ARF CLI

This installs the 'arf' command for accessing all ARF functionality.

Installation:
    pip install -e .

Usage after installation:
    arf --help
    arf memory transmit "GPT-4 is a LLM"
    arf swarm query "What is 47 * 89?"
    arf ontology validate "(GPT-4, is_a, LLM)"
    arf benchmark --suite memory --iterations 10
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text()
else:
    long_description = "ARF - FLOSSI0ULLK Agent Runtime Framework"

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
else:
    requirements = [
        "numpy>=1.24.0",
        "sentence-transformers>=2.2.0",
        "torch>=2.0.0",
        "pytest>=7.0.0",
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
    ]

# Optional dependencies for specific features
extras_require = {
    "swarm": [
        "aiohttp>=3.9.0",
    ],
    "bridge": [
        "pyyaml",
        "h5py",
        "websockets>=10.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "black>=23.0.0",
        "ruff>=0.1.0",
    ],
}

# "all" includes everything
extras_require["all"] = list(set(
    dep for extra_deps in extras_require.values() for dep in extra_deps
))

setup(
    name="arf",
    version="0.1.0",
    description="ARF CLI - FLOSSI0ULLK Agent Runtime Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FLOSSI0ULLK Development Team",
    author_email="",
    url="https://github.com/jmccardle/FLOSS",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "arf=cli.main:cli_main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    keywords="arf flossi0ullk ai agents swarm ontology cli",
)
