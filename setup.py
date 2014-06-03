#!/usr/bin/env python


from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="fin",
        version="1.8",
        license="BSD",

        description="A small, useful python utility library",
        author="Steve Stagg",
        author_email="stestagg@gmail.com",
        url="http://github.com/stestagg/fin",

        packages=find_packages("src"),
        package_dir={"": "src"},

        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
        ]

    )
