import hashlib
import re
import subprocess

from setuptools import find_packages, setup

VERSION_NUMBER = "1.2.8"

try:
    GIT_BRANCH = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    GIT_BRANCH = GIT_BRANCH.decode()
    GIT_BRANCH = GIT_BRANCH.rstrip()
except Exception:
    GIT_BRANCH = "master"

def _sanitize_branch(branch: str) -> str:
    """Return a PEP 440 compatible identifier for a branch name."""

    sanitized = re.sub(r"[^a-z0-9]+", ".", branch.lower()).strip(".")
    return sanitized


def _branch_dev_suffix(branch: str) -> int:
    """Generate a deterministic integer suffix for development releases."""

    digest = hashlib.sha1(branch.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 10000 + 1

if GIT_BRANCH == "master":
    DEVELOPMENT_STATUS = "Development Status :: 5 - Production/Stable"
    VERSION_NAME = VERSION_NUMBER
elif GIT_BRANCH == "beta":
    DEVELOPMENT_STATUS = "Development Status :: 4 - Beta"
    VERSION_NAME = f"{VERSION_NUMBER}b0"
elif GIT_BRANCH == "dev":
    DEVELOPMENT_STATUS = "Development Status :: 3 - Alpha"
    VERSION_NAME = f"{VERSION_NUMBER}.dev0"
else:
    sanitized_branch = _sanitize_branch(GIT_BRANCH) or "prealpha"
    print(
        f"Unknown git branch '{sanitized_branch}', using pre-alpha development version"
    )
    DEVELOPMENT_STATUS = "Development Status :: 2 - Pre-Alpha"
    VERSION_NAME = f"{VERSION_NUMBER}.dev{_branch_dev_suffix(sanitized_branch)}"


def readme_type() -> str:
    import os
    if os.path.exists("README.rst"):
        return "text/x-rst"
    if os.path.exists("README.md"):
        return "text/markdown"


def readme() -> [str]:
    with open('README.rst') as f:
        return f.read()


def install_requirements() -> [str]:
    return read_requirements_file("requirements.txt")


def test_requirements() -> [str]:
    return read_requirements_file("test_requirements.txt")


def read_requirements_file(file_name: str):
    with open(file_name, encoding='utf-8') as f:
        requirements_file = f.readlines()
    return [r.strip() for r in requirements_file]


setup(
    name='raspyrfm_client',
    version=VERSION_NAME,
    description='A library to send rc signals with the RaspyRFM module',
    long_description=readme(),
    long_description_content_type=readme_type(),
    license='GPLv3+',
    author='Markus Ressel',
    author_email='mail@markusressel.de',
    url='https://github.com/markusressel/raspyrfm-client',
    packages=find_packages(exclude=['tests']),
    package_data={
        "custom_components.raspyrfm": [
            "manifest.json",
            "translations/*.json",
            "frontend/*.js",
        ]
    },
    include_package_data=True,
    classifiers=[
        DEVELOPMENT_STATUS,
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    install_requires=install_requirements(),
    tests_require=test_requirements()
)
