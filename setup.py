import setuptools

with open("README.md", "r", encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="wmt",
    version="0.0.3",
    author="IdanP",
    author_email="idan.kp@gmail.com",
    description="Where is my time?",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/idanpa/whereismytime",
    packages=setuptools.find_packages(),
    install_requires=[
        'onedrivesdk',
	'dateparser',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points = {
        "console_scripts": ['wmt = wmt.wmt:main']
    },
)
