from setuptools import setup, find_packages

setup(
    name="k8s-resource-exporter",
    version="1.0.0",
    description="Export Kubernetes cluster resources to YAML, JSON, or HTML reports",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Danilo Vera",
    url="https://github.com/danilovera36/k8s-resource-exporter",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "kubernetes>=28.1.0",
        "click>=8.1",
        "jinja2>=3.1",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "k8s-exporter=k8s_exporter.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
