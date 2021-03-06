import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(name='mediathekDownloader',
      version='1.0.2',
      description=' Downloads series and movies from German public media libraries (Öffentlich-Rechtliche Sender) to your Synology NAS, for use with Synology Video Station.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/TomMeHo/mediathekDL',
      author='Thomas Meder',
      author_email='tom@tommho.net',
      license='BSD',
      packages=setuptools.find_packages(),
      zip_safe=False,
      install_requires=[
            'datetime >= 4.3',
            'cli-logger >= 1.0',
            'feedparser >= 6.0',
            'vsmetaEncoder >= 0.1',
            'wget >= 3.2'
      ],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Logging"
      ],
      python_requires='>=3.6'
)