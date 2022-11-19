# bd.hooks

This package allows to extend API functionality using hook modules.

## Usage

/your/directory/with/hooks/sum_hook.py

```python
def sum(a, b):
    return a + b


def sub(a, b):
    return a - b


def register(registry):
    registry.add_hook('calc', sum, priority=20)
    registry.add_hook('calc', sub, priority=60)

```

.../app.py

```python
from bd.hooks import load, execute

# first we have to load all the hooks
# in directory and store them in cache
load('/your/directory/with/hooks')


def result_callback(result):
    """Get every hook's execution result and do something with it."""
    pass


# execute all registered hooks ordered
# by their priority (start from hooks with highest priority)
# and pass result to 'result_callback' on each hook execution
execute('calc', 10, 7).all(result_callback)     # results will be 3 and 17

# execute only the first hook by priority
result = execute('calc').one()      # result will be 3

```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository]

## Authors

* **Heorhi Samushyia**

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
