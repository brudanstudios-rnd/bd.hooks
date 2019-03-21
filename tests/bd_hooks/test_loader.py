import pytest
import mock

from bd_hooks import loader


class GetSearchPathTests:

    def test_find_directories_recursively(self, fs):
        fs.create_dir('/root/a/b/c')
        expected = ['/root', '/root/a', '/root/a/b', '/root/a/b/c']
        actual = loader.get_searchpath('/root')
        print actual == expected