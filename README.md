## Setup

### Docker - deployment

```shell
git clone https://github.com/jmy12k3/crypto-miner.git
cd crypto-miner/
docker compose up -d
```

Remove ```-d``` for running in attached mode

### Conda - development

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

1. Add function annotation if the type of return cannot be identified by IDE

2. Always add type hints on function parameters
   - Use ```typing.Annotate``` if the specified class cannot be type-hinted

3. Always add the most detailed type hints if possible

4. Always assign the default value directly for parameters with single type

### Importing

5. Use ```import ...```  when importing modules from the python standard library
   - Use ```from ... import ``` when importing classes and decorators from the python standard library

6. Always use ```from ... import ...``` for third-party libraries

7. Always use relative imports when importing local files from the same folder

8. Always use absolute imports when importing local files from the different folder

### Disabling linters

9. For ```# noqa: ... ``` and ```# type: ignore```, this should only be used on niche lines

   - board exception (flake8)

   - wildcard imports (flake8)

   - reusing variable name (mypy)

   - the place where it is impossible to go wrong but mypy keeps yelling for an ```assert``` (mypy)

10. For ```@no_type_check```, this should only be used on functions with module conflicts

11. For ```# mypy: disable-error-code=...```, this should only be used when mypy keeps yelling to code that works



## End

```
BAT
ICX
OMG
ONT
QTUM
```

```
FTT
SRM
```
