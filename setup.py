from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

TESTS_REQUIRE = ["selenium~=3.141", "pylint", "mock", "black", "bandit"]

setup(
    name="webviz_sumo_experiments",
    description="Webviz sumo experiments",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    entry_points={
        "webviz_config_plugins": [
            "SumoTimeSeries = webviz_sumo_experiments.plugins:SumoTimeSeries",
        ]
    },
    install_requires=[
        "webviz-config>=0.5.0",
        "fmu-sumo@git+https://github.com/equinor/fmu-sumo@master",
        "sumo-wrapper-python@git+https://github.com/equinor/sumo-wrapper-python.git@master",
        "h11==0.11",  # ERROR: httpcore 0.15.0 has requirement h11<0.13,>=0.11, but you'll have h11 0.14.0 which is incompatible.
    ],
    tests_require=TESTS_REQUIRE,
    extras_require={"tests": TESTS_REQUIRE},
    setup_requires=["setuptools_scm~=3.2"],
    python_requires="~=3.6",
    use_scm_version=True,
    zip_safe=False,
    classifiers=[
        "Natural Language :: English",
        "Environment :: Web Environment",
        "Framework :: Dash",
        "Framework :: Flask",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
