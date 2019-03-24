import os
import pytest
import mock

from bd_hooks import loader


class GetSearchPathTests:

    def test_finds_directories_recursively(self, fs):
        fs.create_dir(os.path.join('root', 'a', 'b', 'c'))
        expected = [
            'root',
            os.path.join('root', 'a'),
            os.path.join('root', 'a', 'b'),
            os.path.join('root', 'a', 'b', 'c')
        ]
        actual = loader.get_searchpath('root')
        assert actual == expected

    def test_finds_only_directories(self, fs):
        fs.create_dir(os.path.join('root', 'a', 'b', 'c'))
        fs.create_file(os.path.join('root', 'a', 'file.py'))
        expected = [
            'root',
            os.path.join('root', 'a'),
            os.path.join('root', 'a', 'b'),
            os.path.join('root', 'a', 'b', 'c')
        ]
        actual = loader.get_searchpath('root')
        assert actual == expected


class HookLoaderTests:

    class LoadTests:

        def test_returns_none_on_missing_search_paths(self):
            result = loader.load(None)
            assert result is None

        @mock.patch.object(loader.PluginBase, 'make_plugin_source')
        def test_extends_search_paths_with_environment_variable(self, mock_makepluginsource, fs):
            mock_pluginsource = mock.Mock()
            mock_pluginsource.list_plugins.return_value = []
            mock_makepluginsource.return_value = mock_pluginsource

            search_paths = [os.path.join('a', 'b', 'c'), os.path.join('d', 'e', 'f')]
            list(map(fs.create_dir, search_paths))

            with mock.patch('bd_hooks.loader.os.getenv', return_value=os.pathsep.join(search_paths)) as mock_getenv:
                loader.load(None)

            mock_getenv.assert_called_once_with('BD_HOOKPATH')
            mock_makepluginsource.assert_called_with(
                searchpath=search_paths,
                persist=True
            )

        def test_returns_none_on_non_existing_search_paths(self, fs):
            search_paths = [os.path.join('a', 'b', 'c'), os.path.join('d', 'e', 'f')]
            result = loader.load(None, search_paths)
            assert result is None

        @mock.patch.object(loader.PluginBase, 'make_plugin_source')
        def test_finds_paths_with_no_oserrors(self, mock_makepluginsource, fs):

            mock_pluginsource = mock.Mock()
            mock_pluginsource.list_plugins.return_value = []
            mock_makepluginsource.return_value = mock_pluginsource

            search_paths = [os.path.join('a', 'b', 'c'), os.path.join('d', 'e', 'f')]
            list(map(fs.create_dir, search_paths))

            with mock.patch('bd_hooks.loader.get_searchpath', side_effect=[OSError, [search_paths[1]]]) as mock_getsearchpath:
                result = loader.load(None, search_paths)

            assert result is None
            mock_getsearchpath.assert_has_calls(list(map(mock.call, search_paths)))
            assert mock_getsearchpath.call_count == 2
            mock_makepluginsource.assert_called_with(
                searchpath=[search_paths[1]],
                persist=True
            )

        def test_loads_plugins(self, temp_dir_creator):
            search_paths = [temp_dir_creator(), temp_dir_creator()]

            for i, search_path in enumerate(search_paths):
                plugin_path = os.path.join(search_path, 'plugin_{}.py'.format(i))
                with open(plugin_path, 'w') as f:
                    f.write(
                        '\n'
                        'def register(registry):\n'
                        '    registry("plugin_{}")\n'.format(i)
                    )

            mock_registry = mock.Mock()

            loader.load(mock_registry, search_paths)

            mock_registry.assert_called()
            assert mock_registry.call_count == 2
            mock_registry.assert_has_calls([mock.call('plugin_0'), mock.call('plugin_1')])

        def test_skips_failed_to_load_plugins(self, temp_dir_creator):
            search_paths = [temp_dir_creator(), temp_dir_creator()]

            plugin_path = os.path.join(search_paths[0], 'plugin_0.py')
            with open(plugin_path, 'w') as f:
                # making syntax error
                f.write(
                    '\n'
                    'def register(registry):\n'
                    '    registry(")\n'
                )

            plugin_path = os.path.join(search_paths[1], 'plugin_1.py')
            with open(plugin_path, 'w') as f:
                f.write(
                    '\n'
                    'def register(registry):\n'
                    '    registry("plugin_1")\n'
                )

            mock_registry = mock.Mock()

            loader.load(mock_registry, search_paths)

            mock_registry.assert_called_once_with('plugin_1')

        def test_skips_plugins_with_no_register_function(self, temp_dir_creator):
            search_paths = [temp_dir_creator(), temp_dir_creator()]

            plugin_path = os.path.join(search_paths[0], 'plugin_0.py')
            with open(plugin_path, 'w') as f:
                # making mistake in function name
                f.write(
                    '\n'
                    'def n_register(registry):\n'
                    '    registry("plugin_0")\n'
                )

            plugin_path = os.path.join(search_paths[1], 'plugin_1.py')
            with open(plugin_path, 'w') as f:
                f.write(
                    '\n'
                    'def register(registry):\n'
                    '    registry("plugin_1")\n'
                )

            mock_registry = mock.Mock()

            loader.load(mock_registry, search_paths)

            mock_registry.assert_called_once_with('plugin_1')

        def test_skips_failed_to_registed_plugins(self, temp_dir_creator):
            search_paths = [temp_dir_creator(), temp_dir_creator()]

            plugin_path = os.path.join(search_paths[0], 'plugin_0.py')
            with open(plugin_path, 'w') as f:
                # making mistake in function name
                f.write(
                    '\n'
                    'def register(registry):\n'
                    '    raise Exception()\n'
                )

            plugin_path = os.path.join(search_paths[1], 'plugin_1.py')
            with open(plugin_path, 'w') as f:
                f.write(
                    '\n'
                    'def register(registry):\n'
                    '    registry("plugin_1")\n'
                )

            mock_registry = mock.Mock()

            loader.load(mock_registry, search_paths)

            mock_registry.assert_called_once_with('plugin_1')