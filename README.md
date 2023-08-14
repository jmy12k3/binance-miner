# Crypto-miner

Buffett in your Pi!



## Deployment

...



## Style guidelines

For the sake of better maintainencing, please follow the style guideline

### Type hints

1. Always add type hint on function parameters
    - Annotate if you cannot type hint that specific class
2. Always add the most detailed type hints if possible
    - e.g., ```dict[str, int]``` is always better than ```dict```, ```dict[str, Any]``` or ```dict[Any, str]```
3. Add function annotation ```->``` if the type of return cannot be identified by IDE
4. Always assign the default value directly, without type hint to a single-type parameter
    - Bad example
      - ```def my_function(my_param: int = 1): ...```
    - Good example
      -  ```def my_function(my_param=1): ...```
    - In this case, ```my_param``` has a default value, and can only be ```int```, so we directly assign it instead of type-hinting

### Importing

5. Always use ```import ...``` for the python standard library
   - Except when importing classes and decorators

6. Always use ```from ... import ...``` for third-party libraries

7. Always use ```from ... import ...``` for local modules

### Disabling linters

8. For ```# type: ignore``` and ```# noqa: ...```, this should only be used on niche cases
   - disabling board exception linting (flake8)
   - wildcard imports (flake8)
   - redundant errors when reusing variable name (mypy)
   - the place where it is impossible to go wrong but mypy keeps yelling for ```assert``` (mypy)

> Line level

-----



9. For ```@no_type_check```, this should only be used on module conflicts

> Function level

-----



10. For ```# mypy: disable-error-code: ...```, this should only be used when the error is popping out globally

> Global level

-----



## Reserved watchlist

> Coins with potential

```
BAT
ICX
OM
ONT
QTUM
```

> TODO: Find replacement of these coins

```
FTT
SRM
```
