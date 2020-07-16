import setuptools

setuptools.setup(
    name="jagerbot",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author='Grayson Head',
    author_email='grayson@graysonhead.net',
    license='GPL V3',
    packages=setuptools.find_packages(),
    install_requires=[
        'discord.py==1.3.3',
        'snips-nlu==0.20.2',
        'snips-nlu-en==0.2.3',
        'SQLAlchemy==1.3.18',
        'EsiPy==1.0.0'
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/x-rst',
)