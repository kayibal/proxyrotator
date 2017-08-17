import versioneer
from setuptools import find_packages, setup

packages = find_packages()

setup(name='proxy-rotator',
      version=versioneer.get_version(),
      description='proxy-rotator: smart and efficient rotating of proxies',
      url='http://github.com/kayibal/proxy-rotator',
      author='Alan Höng',
      author_email='alan.f.hoeng@gmail.de',
      install_requires=["requets"],
      test_requires=["pytest"],
      cmdclass=versioneer.get_cmdclass(),
      packages=packages,
      zip_safe=False)
