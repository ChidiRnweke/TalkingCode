from setuptools import find_packages, setup

setup(
    name="chatGITpt",
    packages=find_packages(exclude=["chatGITpt_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
