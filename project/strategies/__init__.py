import os
from importlib.util import module_from_spec, spec_from_file_location


def get_strategy(name):
    for dirpath, _, filenames in os.walk(os.path.dirname(__file__)):
        for filename in filenames:
            if not (filename.endswith(".py") and filename.replace(".py", "") == name):
                continue
            location = os.path.join(dirpath, filename)
            spec = spec_from_file_location(name, location)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.Strategy
    return None
