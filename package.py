name = "bd.hooks"

version = "v0.1.13"

build_command = "python -m rezutil build {root}"
private_build_requires = ["rezutil"]


def commands():
    env.PYTHONPATH.append("{root}/python")
