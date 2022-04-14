import setuptools
import pathlib


here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setuptools.setup(
    name="chronometer",
    version="1.0.0",
    author="rothman857",
    author_email="rothman857@gmail.com",
    description="Chronometer Time Display",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rothman857/chronometer",
    project_urls={
        "Bug Tracker": "https://github.com/rothman857/chronometer/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages('src'),
    python_requires=">=3.8",
    install_requires=['pytz']
)
