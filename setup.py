from setuptools import setup

setup(
    name='snapshotalyzer',
    version='0.1',
    author='Jack Farrell',
    author_email='jfarrell3@wisc.edu',
    description="SnapshotAlyzer is a tool to manage AWS EC2 snapshots",
    license="GPLv3",
    packages=['shotty'],
    url='https://github.com/jackjf28/snapshotalyzer',
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points='''
        [console_scripts]
        shotty=shotty.shotty:cli
    ''',
)