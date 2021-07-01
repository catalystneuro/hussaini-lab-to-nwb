# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

# Get the long description from the README file
with open('README.md', 'r') as f:
    long_description = f.read()

# Get requirements
with open('requirements.txt') as f:
    install_requires = f.read().strip().split('\n')

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
        'klusta',
        'klustakwik2',
        'jupyter',
        'pyqtwebengine',
        'phy',
        'psutil',
        'pyintan',
        'pynwb',
        'pyopenephys',
        'nwb_conversion_tools',
        'spiketoolkit',
        'spikewidgets',
        'spikesorters',
        'spikecomparison',
        'ml_ms4alg',
        'openpyxl',
        'numba',
        'tridesclous',
        'spyking-circus',
        'opencv-python'
    ],
    dependency_links=[
        'git+https://github.com/SpikeInterface/spikeextractors@118aa9d2acb395e76bcb40c80a9db6f28a054230#egg=spikeextractors',
        'git+https://github.com/NeuralEnsemble/python-neo.git@3d8b139bbf0bc3193bf576ee707575a43bf181c3#egg=neo',
    ]
)
