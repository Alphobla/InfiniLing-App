from setuptools import setup, find_packages

setup(
    name="unified-language-app",
    version="0.1.0",
    author="Valentin Maissen",
    author_email="your_email@example.com",
    description="A unified application for audio transcription and vocabulary learning.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/unified-language-app",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai-whisper",
        "mutagen",
        "tkinter",
        "pandas",
        "numpy",
        "requests",
        "flask"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)