from setuptools import setup
from CCI_Baseline.CCI_Baseline import version
setup(
    name='CCI_Baseline',
    version=version,
    packages=['CCI_Baseline'],
    url='https://github.com/w2oanalytics/cci_baseline',
    license='',
    author='jharris',
    author_email='jharris@realchemistry.com',
    description='A package to calculate CCI and create baseline tables',
    install_requires=['pandas', 'requests', 'datetime', 'tqdm',
                      'boto3', 'numpy', 'google', 'os',
                      'collections', 'copy', 'itertools']
)