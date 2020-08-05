import os
from distutils.core import setup

requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")

with open(requirements_path) as file_object:
    requirements = file_object.readlines()

setup(
    name="aws-console",
    version="0.1",
    author="Sebastian Blask",
    description=(
        "Opens the AWS Console authenticating you with your access key"
        " instead of user name and password"
    ),
    py_modules=["aws_console"],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'aws-console=aws_console:main',
        ],
    },
)
