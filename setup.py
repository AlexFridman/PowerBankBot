import os

from setuptools import setup


def reqs(f):
    return filter(None, (l.split('#', 1)[0].strip() for l in open(os.path.join(os.getcwd(), f))
                         if not l.startswith('--')))


setup(
    name='powerbank_bot',
    author='alfrid',
    install_requires=reqs('requirements.txt'),
    entry_points={
        'console_scripts': [
            'run_bot=powerbank_bot.main:main'
        ]
    }
)
