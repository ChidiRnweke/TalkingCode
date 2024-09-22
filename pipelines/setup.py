from setuptools import find_packages, setup

setup(
    name="TalkingCode",
    packages=find_packages(exclude=["TalkingCode_tests"]),
    install_requires=["dagster", "dagster-cloud"],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
