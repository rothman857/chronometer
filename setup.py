import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()



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