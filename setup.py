# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

# Get the long description from the README file
with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='hussaini_lab_to_nwb',
    version='0.1.0',
    description='NWB conversion scripts and tutorials.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Steffen Buergers, Julia Sprenger, Alessio Buccino and Ben Dichter',
    email='ben.dichter@gmail.com',
    url='https://github.com/catalystneuro/hussaini-lab-to-nwb',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.yml', '*.json']},
    install_requires=[
        'pandas',
        'numpy',
        'h5py',
        'cython',
        'tqdm',
        'click',
        'pillow',
        'scipy',
        'matplotlib',
        'seaborn',
        'scikit-learn',
        'pyqt5',
        'nose',
        'jupyter',
        'pyqtwebengine',
        'phy',
        'psutil',
        'pyintan',
        'pynwb',
        'nwb_conversion_tools',
        'spikeextractors',
        'spiketoolkit',
        'spikewidgets',
        'spikesorters',
        'spikecomparison'
    ]
)
