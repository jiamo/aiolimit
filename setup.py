try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os.path
import re

VERSION_RE = re.compile(r"""__version__ = ['"]([-a-z0-9.]+)['"]""")
BASE_PATH = os.path.dirname(__file__)


with open(os.path.join(BASE_PATH, "aiolimit", "__init__.py")) as f:
    try:
        version = VERSION_RE.search(f.read()).group(1)
    except IndexError:
        raise RuntimeError("Unable to determine version.")


with open(os.path.join(BASE_PATH, "README.md")) as readme:
    long_description = readme.read()


setup(
    name="aiolimit",
    description="async api limit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    version=version,
    author="jiamo",
    author_email="life.130815@gmail.com",
    maintainer="jiamo",
    maintainer_email="life.130815@gmail.com",
    url="https://github.com/jiamo/aiolimit",
    packages=["aiolimit"],
    python_requires=">=3.6",
    install_requires=["aioredis"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "coverage", "pytest-cov", "pytest-asyncio"],
)
