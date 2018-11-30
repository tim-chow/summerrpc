from setuptools import setup, find_packages

setup(
    name="summerrpc",
    version="4.0.0",
    packages=find_packages(),

    install_requires=[
        "tornado",
        "futures",
        "zkpython",
        "netifaces",
        "requests",
        "redis",
        "msgpack"
    ],

    test_suite="summerrpc_tests",

    author="Tim Chow",
    author_email="jordan23nbastar@vip.qq.com",
    description="An RPC framework based on Tornado",
    license="MIT",
    keywords="summerrpc rpc service-discovery service-registry",
    url="http://timd.cn/summerrpc"
)
