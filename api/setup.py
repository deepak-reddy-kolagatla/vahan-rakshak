from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vahan-rakshak",
    version="0.1.0",
    author="Hackathon Team",
    description="Project Vāhan-Rakshak: Multi-Agent Vehicle Safety Guardian System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/korrapati-satish/vahan-rakshak",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.10.3,<3",
        "python-dotenv>=1.0.0",
    "requests>=2.32.0,<3",
    "fastapi>=0.115.0,<1.0",
        "uvicorn>=0.24.0",
        "paho-mqtt>=1.6.1",
        "Flask>=3.0.0",
    "redis>=6.0.0",
        "pyyaml>=6.0.2,<7.0.0",
        "qrcode>=7.4.2",
        "pillow>=10.1.0",
        "numpy>=1.26.2",
        "ibm-watsonx-orchestrate>=1.14.0",
    ],
)
