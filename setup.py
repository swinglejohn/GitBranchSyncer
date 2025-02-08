from setuptools import setup

setup(
    name="gitbranchsyncer",
    version="0.1.0",
    description="A utility to sync git branches with remote changes",
    author="swinglejohn",
    py_modules=["gitbranchsyncer"],
    install_requires=[
        "gitpython>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "git-branch-syncer=gitbranchsyncer:main",
        ],
    },
    python_requires=">=3.6",
)
