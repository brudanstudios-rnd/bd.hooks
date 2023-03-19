name = "bd.hooks"

version = "0.1.16"

build_command = "python -m rezutil build {root}"
private_build_requires = ["rezutil"]


def commands():
    env.PYTHONPATH.append("{root}/python")
