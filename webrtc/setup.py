from setuptools import setup, find_packages

setup(
    name="mylibrary",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Flask',
        'firebase-admin'
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple Flask app with Firebase video upload functionality",
    url="https://github.com/yourusername/mylibrary",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
