import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kao",
    version="0.0.1",
    author="Mia Chono",
    description="A Python Downloader of manwha and manga scans",
    license="MIT",
    url="https://github.com/mia-chono/kao",
    install_requires=[
        "requests",
        "requests_html",
        "img2pdf",
        "cloudscraper",
        "beautifulsoup4",
        "lxml",
        "bs4",
        "Pillow",
        "validators",
    ],
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.9",
)
