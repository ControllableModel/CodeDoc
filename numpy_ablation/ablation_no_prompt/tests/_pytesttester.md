# Class Constructor Documentation

## `__init__(self, module_name)`

This is the constructor method for the class that initializes a new instance with a specified module name.

### Parameters

- `module_name` (str): The name of the module. This parameter should be a valid string that represents the name of the module the class instance will be associated with.

### Behavior

- Upon instantiation of the class, the `module_name` is stored as an instance attribute (`self.module_name`).
- The special attribute `__module__` is set to the value of `module_name`, which can be used to identify the module context of the class.

### Example Usage

```python
# Creating an instance of the class with a specified module name
my_instance = MyClass("example_module")

# Access the module name
print(my_instance.module_name)  # Output: example_module

# Access the special module attribute
print(my_instance.__module__)  # Output: example_module
```

### Notes

- Ensure that the provided `module_name` is meaningful within the context of your application to maintain clarity in module management.
- This constructor is typically part of a larger class definition, which may include additional methods and attributes.

### Related Functions

- This constructor may interact with other methods within the same class that depend on the `module_name` attribute.
- If there are methods that utilize `self.module_name`, they should be documented in conjunction with this constructor.

# NumPy Testing Function Documentation

## Function: `__call__`

### Purpose
This function is designed to run tests for a given NumPy module using the `pytest` framework. It allows the user to specify which tests to run, adjust verbosity, and include additional arguments or coverage options.

### Parameters
- **label** (`str`, optional): 
  - Determines which tests to execute. 
  - Accepted values:
    - `'fast'`: Skips tests marked with `pytest.mark.slow`.
    - `'full'`: Ignores the slow marker entirely.
  - Default is `'fast'`.

- **verbose** (`int`, optional): 
  - Controls the level of detail in test output.
  - Valid range: `1` to `3`. 
  - Default is `1`.

- **extra_argv** (`list`, optional): 
  - A list of additional command-line arguments to be passed to `pytest`.

- **doctests** (`bool`, optional): 
  - This option is currently not supported.
  
- **coverage** (`bool`, optional): 
  - If set to `True`, generates a coverage report for the NumPy code. 
  - Requires the installation of the `pytest-cov` plugin. 
  - Default is `False`.

- **durations** (`int`, optional): 
  - Controls which test duration information to report.
  - Values:
    - `< 0`: No duration reporting.
    - `0`: Report duration of all tests.
    - `> 0`: Report duration of the slowest tests.
  - Default is `-1`.

- **tests** (`test` or `list of tests`, optional): 
  - Specifies the tests to be executed. If `None`, defaults to the current module.

### Returns
- **result** (`bool`): 
  - Returns `True` if all tests pass, `False` otherwise.

### Notes
- Each NumPy module provides a `test` function in its namespace to facilitate running tests. For example, to run all tests for `numpy.lib`, use:
  ```python
  np.lib.test() #doctest: +SKIP
  ```

### Examples
```python
# Running all tests with default parameters
result = np.lib.test() #doctest: +SKIP
# Example output
# 1023 passed, 2 skipped, 6 deselected, 1 xfailed in 10.39 seconds
print(result) # Returns True if tests were successful.
```

### Important Note
- The `doctests` parameter is mentioned in the documentation but is currently not supported. Users should utilize other test configurations instead.

## Dependency
### Function: `_show_numpy_info`
The `_show_numpy_info()` function is a helper function that prints version information about NumPy and its CPU feature capabilities. 

### Example Usage
```python
_show_numpy_info()  # Prints out the NumPy version and CPU feature information.
```

## Summary
This comprehensive `__call__` function serves as a flexible interface for running unit tests on NumPy modules, accommodating a variety of user preferences and configurations, while the `_show_numpy_info` function provides supplemental information about the NumPy environment.

# Documentation for `_show_numpy_info()`

## Overview
The `_show_numpy_info()` function provides basic information about the installed NumPy library, including its version and CPU features enabled for optimization.

## Function Signature
```python
def _show_numpy_info():
```

## Description
This function imports the NumPy library and prints out two key pieces of information:
1. The version of NumPy that is currently installed.
2. The CPU features that are enabled for NumPy, if any, or a message indicating that nothing is enabled.

## Usage
To use this function, simply call `_show_numpy_info()`. It does not require any parameters and does not return any values. The output is printed directly to the console.

### Example
```python
_show_numpy_info()
```
**Sample Output:**
```
NumPy version 1.21.0
NumPy CPU features:  SSE2, AVX2
```
(Note: The actual output will vary depending on the installed version of NumPy and the CPU features available.)

## Important Notes
- This function is primarily for informational purposes and is useful for developers who want a quick check on their NumPy installation.
- If NumPy is not installed or accessible, an ImportError may be raised when calling this function.
  
## Dependencies
- The function directly imports NumPy (`import numpy as np`) and depends on the presence of the NumPy library in the Python environment.
- Specifically, it uses the `np.__version__` attribute to get the version number and `np.lib._utils_impl._opt_info()` to access CPU optimization information.

---

# Documentation for `PytestTester.__call__`

## Overview
The `__call__` method of the `PytestTester` class allows you to run tests for a specified module using pytest. It provides various options for configuring the test run, such as verbosity, coverage reporting, and selection of test labels.

## Method Signature
```python
def __call__(self, label='fast', verbose=1, extra_argv=None,
             doctests=False, coverage=False, durations=-1, tests=None):
```

## Parameters
- **label** (`str`, optional): Determines the tests to run:
  - `'fast'`: Skips tests marked with `pytest.mark.slow`.
  - `'full'`: Ignores the slow marker.
  Default is `'fast'`.

- **verbose** (`int`, optional): Controls the verbosity of the test output. Range is 1 (minimal) to 3 (detailed). Default is 1.

- **extra_argv** (`list`, optional): A list of additional arguments to pass to pytest.

- **doctests** (`bool`, optional): Indicates whether to include doctests in the run. Note: This feature is not supported.

- **coverage** (`bool`, optional): If `True`, enables coverage reporting for NumPy code. Default is `False`. Requires `pytest-cov` to be installed.

- **durations** (`int`, optional): Configures reporting of test durations. 
  - `< 0`: Do nothing.
  - `0`: Reports time for all tests.
  - `> 0`: Reports time for the slowest tests. Default is -1.

- **tests** (`test` or `list`, optional): Specifies tests to execute with pytest using the `--pyargs` option. If `None`, all tests for the module are executed.

## Returns
- **result** (`bool`): Returns `True` if the tests ran successfully, otherwise `False`.

## Usage Example
```python
tester = PytestTester()
result = tester(label='full', verbose=2, coverage=True)
print(result)  # Outputs: True or False depending on test results
```

## Important Notes
- Each NumPy module has a `test` function in its namespace which can be called to run all tests for that module, for example: `np.lib.test()`.
- If `doctests` is set to `True`, a warning will be raised mentioning that doctests are not supported.
- The function manages warnings related to NumPy and associated modules to prevent clutter in the output.

## Related Functionality
- The `_show_numpy_info()` function is invoked at the start of this method to display information about the NumPy installation.
- This method depends on the `pytest` library for testing functionality.

By understanding `_show_numpy_info()` and `PytestTester.__call__`, developers can effectively check their NumPy setup and run tests to ensure code integrity within the NumPy environment.

