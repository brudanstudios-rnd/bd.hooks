import os
import tempfile
import shutil
import uuid

import pytest


@pytest.fixture
def temp_dir_creator():
    temp_dir_paths = []

    def _create_temp_dir():

        temp_dir_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        if not os.path.exists(temp_dir_path):
            os.makedirs(temp_dir_path)

        temp_dir_paths.append(temp_dir_path)

        return temp_dir_path

    yield _create_temp_dir

    for temp_dir_path in temp_dir_paths:
        if os.path.exists(temp_dir_path):
            shutil.rmtree(temp_dir_path)

