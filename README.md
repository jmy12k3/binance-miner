# Crypto-miner

Buffett in your Pi!



### Docker

```shell
git clone https://github.com/jmy12k3/crypto-miner.git
cd crypto-miner/
docker compose up -d
```

Remove ```-d``` for running in attached mode

### Conda

Not recommended for deployment, only for development

```
git clone https://github.com/jmy12k3/crypto-miner.git
cd crypto-miner/
conda create --name crypto-miner python=3.10
conda activate crypto-miner
pip install -r requirements.txt
python -m project
```

### Dashboard

Check out [crypto-miner-dashboard](https://github.com/jmy12k3/crypto-miner-dashboard)

## Style guideline

For the sake of better readability, please follow the style guideline

### Type hints

1. Always add type hints on function parameters
    - Use ```typing.Annotate``` if the specified class cannot be type-hinted

2. Always add the most detailed type hints if possible

3. Always assign the default value directly for parameters only with a single type

4. Add function annotation if the type of return cannot be identified by IDE

```python
from collections.abc import Callable
from typing import Annotate, TypeVar
from typing_extensions import ParamSpec

from easydict import Easydict

T = TypeVar("T")
P = ParamSpec("P")

cannot_typehint: Easydict = Easydict({...: ...})
my_dict: dict = {"the_answer_to_anything", 42}

# Rule 1 - Add type hints
def my_function(my_dict: Annotate[Easydict, cannot_typehint]): ...

# Rule 2 - Add type hints as detailed as possible
def my_function(my_dict: dict[str, int]): ...

# Rule 3 - Assign the default value directly for parameters only with a single type
def my_function(my_dict: dict[str, int], my_int=42): ...

# Rule 4 - Add function annotation for unidentifiable returns
def my_function(fun: Callable[P, T], *args, **kwargs) -> Callable[P, T]:
    return fun(*args, **kwargs)
```

### Importing

5. Always use ```import ...``` for the python standard library
   - Except when importing classes and decorators

6. Always use ```from ... import ...``` for third-party libraries

7. Always use ```from ... import ...``` for local modules

### Disabling linters

8. For ```# type: ignore``` and ```# noqa: ...```, this should only be used on niche <font size="30">lines</font>

   - board exception (flake8)

   - wildcard imports (flake8)

   - reusing variable name (mypy)
   - the place where it is impossible to go wrong but mypy keeps yelling for ```assert``` (mypy)

9. For ```@no_type_check```, this should only be used on <font size="30">functions</font> with module conflicts

10. For ```# mypy: disable-error-code=...```, this should only be used when the error is popping out <font size="30">globally</font>

## End

```
BAT
ICX
OM
ONT
QTUM
```

```
FTT
SRM
```
