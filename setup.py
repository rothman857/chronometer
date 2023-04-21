import setuptools
import pathlib
import sys

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")
install_requires = ["pytz", "types-pytz"]
if sys.version_info.minor == 6:
    install_requires.append("dataclasses")

setuptools.setup(
    name="chronometer",
    version="1.0.3",
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
    packages=setuptools.find_packages("src"),
    python_requires=">=3.6",
    install_requires=install_requires,
    package_data={"": ["files/*"]},
    include_package_data=True,
)
