from setuptools import find_packages
from setuptools import setup

setup(
    name='yamp',
    version='0.1',
    author='Alexander Makeenkov',
    author_email='whoami.tut@gmail.com',
    url='https://github.com/amakeenk/yamp',
    description='Unofficial player for Yandex.Music',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts':
            ['yamp = yamp.main:main']
        }
)
