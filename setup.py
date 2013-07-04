from setuptools import setup, find_packages


setup(
    name='sphinxit',
    version='0.3.1',
    author='Roman Semirook',
    author_email='semirook@gmail.com',
    packages=find_packages(),
    license='BSD',
    url='https://github.com/semirook/sphinxit',
    description='Lite and powerful SphinxQL query constructor',
    long_description='Lite and powerful SphinxQL query constructor',
    install_requires=[
        "six >= 1.1.0",
        "oursql >= 0.9.3",
        "ordereddict >= 1.1",
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
