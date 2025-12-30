"""Setup configuration for LLM Tester."""
from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="llm-tester",
    version="0.2.0",
    author="autrion",
    description="Industry-standard LLM security testing toolkit - NMAP for LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/autrion/llm_tester",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.11",
    install_requires=[
        # No external dependencies - stdlib only!
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "llm-tester=llm_tester.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
    ],
    keywords="llm security testing red-team vulnerability assessment ai ml",
    project_urls={
        "Bug Reports": "https://github.com/autrion/llm_tester/issues",
        "Source": "https://github.com/autrion/llm_tester",
        "Documentation": "https://github.com/autrion/llm_tester#readme",
    },
    include_package_data=True,
    package_data={
        "llm_tester": [
            "prompt_library/*.txt",
            "prompts_extended.txt",
        ],
    },
)
