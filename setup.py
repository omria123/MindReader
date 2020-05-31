from setuptools import setup, find_packages

with open('requirements.txt') as f:
	required = f.read().splitlines()

setup(
	name='MindReader',
	version='1.0.0',
	author='Omri Avisar',
	description='Mind reading package',
	packages=find_packages(),
	python_requires='>=3.6',
	install_requires=required,
	tests_require=['pytest'],
)
