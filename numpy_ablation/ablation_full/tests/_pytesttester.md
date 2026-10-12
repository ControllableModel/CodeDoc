# `PytestTester.__init__`

## Metadata
- **FilePath:** `Small-Size\numpy\_pytesttester.py`
- **Version:** 1.0.0
- **Last Updated:** October 2023
- **Audience:** Python developers using NumPy for testing
- **Information Type:** Reference

## About
The `PytestTester.__init__` function initializes an instance of the `PytestTester` class, setting up the testing module's name for subsequent operations.

## Description
This constructor method belongs to the `PytestTester` class within the NumPy library. It assigns the provided `module_name` to both an instance attribute and a private attribute, which can be used for internal representation or processing within the class. Typically, this method is invoked when creating a new instance of the tester, enabling the user to set the context for testing in their modules.

## Parameters
- **module_name** (str): The name of the module to be tested.
  - **Defaults:** None
  - **Constraints:** Must be a valid string representing a module name.

## Returns
- **None:** This method does not return any value.

## Example Usage
```python
# Create an instance of PytestTester for a specific module
tester = PytestTester("mymodule")

# The instance's attributes can be accessed 
print(tester.module_name)  # Expected output: "mymodule"
```

## Prerequisites
- **Environment:** Python 3.6 or newer
- **Dependencies:** NumPy package must be installed.
- **Configuration:** No specific configuration is required beyond having NumPy installed.
- **Access:** User should have access to the NumPy library.

## Related Functions
- **Uses:** 
  - `PytestTester.run_tests`: Initiates the testing process for the designated module.
- **Used By:** 
  - User-defined scripts or tests that require initializing `PytestTester`.
- **See Also:** 
  - `PytestTester`: Class documentation for additional methods and properties.

## Troubleshooting
- **Issue:** Instantiation fails due to an invalid module name.
  - **Solution:** Ensure that the `module_name` is a non-empty string representing an actual Python module.

## Safety & Warnings
- **Warning:** Providing an incorrect module name may lead to unexpected behavior or failures during testing.
- **ℹCaution:** Make sure to follow naming conventions for Python modules to avoid import errors.

## Change Log
| Version | Date          | Changes                       |
|---------|---------------|-------------------------------|
| 1.0.0   | October 2023  | Initial creation of documentation. |

## Accessibility Notes
- The function and its parameters are designed to be accessible through standard programming interfaces in Python.
- Screen readers should effectively read this function's name and parameters as they follow standard naming conventions.

# `PytestTester.__call__`

## Metadata
- **FilePath:** `Small-Size\numpy\_pytesttester.py`
- **Version:** 1.0.0
- **Last Updated:** October 2023
- **Audience:** Developers using NumPy for testing
- **Information Type:** Procedural

## About
The `__call__` method of the `PytestTester` class is designed to execute tests within a module using the `pytest` framework. It enables developers to conveniently run either fast or comprehensive tests, manage test verbosity, and control other execution parameters.

## Description
This function facilitates the execution of tests for the associated module using the `pytest` testing framework. Users can customize the test run by specifying parameters like verbosity, which tests to run, and whether to include coverage reporting. This method is essential for maintaining the integrity of code when working on packages like NumPy, as it allows for efficient test management and reporting.

## Parameters
- **label** (`str`, optional): 
  - Identifies which tests to run. Possible values are:
    - `'fast'`: Skips tests marked with `pytest.mark.slow`.
    - `'full'`: Executes all tests, ignoring the slow marker.
  - **Default:** `'fast'`

- **verbose** (`int`, optional): 
  - Controls the verbosity of test output. Valid values are in the range 1-3.
  - **Default:** `1`

- **extra_argv** (`list`, optional): 
  - A list of additional arguments to pass to `pytest`.
  - **Default:** `None`

- **doctests** (`bool`, optional):
  - **Note:** Not supported.
  - **Default:** `False`
  
- **coverage** (`bool`, optional): 
  - When `True`, reports the code coverage for the NumPy library, necessitating the installation of `pytest-cov`.
  - **Default:** `False`

- **durations** (`int`, optional): 
  - Controls the reporting of test durations:
    - `< 0`: No action taken.
    - `0`: Reports time for all tests.
    - `> 0`: Reports the time of the slowest tests.
  - **Default:** `-1`

- **tests** (`test` or `list`, optional): 
  - Specifies the tests to be executed with the `--pyargs` option of `pytest`.
  - **Default:** `None`

## Returns
- **Type:** `bool`
- **Description:** Returns `True` if all specified tests pass, `False` otherwise.

## Example Usage
```python
# Example of running all tests in the numpy.lib module
import numpy as np

# Run tests
result = np.lib.test()  # doctest: +SKIP
# Expected Output: 
# 1023 passed, 2 skipped, 6 deselected, 1 xfailed in 10.39 seconds
# Check the result of the test run
print(result)  # Expected output: True
```

## Prerequisites
- **Environment:** Python 3.6 or later
- **Dependencies:** 
  - `pytest`
  - `pytest-cov` (if coverage is to be reported)
  
- **Configuration:** Ensure all test cases are properly marked and that pytest is installed in the Python environment.
  
- **Access:** Must have permissions to read and execute tests within the module paths.

## Related Functions
- **Uses:** 
  - Calls `_show_numpy_info` to display NumPy version and CPU features.
  
- **Used By:** 
  - Typically invoked within NumPy library testing functions like `np.lib.test()`.

- **See Also:**
  - Documentation for `pytest` for more advanced capabilities.

## Troubleshooting
- **Issue:** Tests fail or return `False`.
  - **Solution:** Check the test setup, ensure that pytest is correctly installed, and review any output logs for specific errors.

- **Issue:** Coverage reporting does not function.
  - **Solution:** Ensure that `pytest-cov` is installed and correctly configured.

## Safety & Warnings
- **Warning:** Ensure to address all warnings filtered during test runs, as they can indicate underlying issues.
- **ℹCaution:** Running tests with `label='full'` may include longer-running tests and should be executed thoughtfully in resource-constrained environments.
- **Note:** Always run tests in a development environment before deploying changes to production. 

## Change Log
| Version | Date        | Changes               |
|---------|-------------|-----------------------|
| 1.0.0   | October 2023| Initial documentation  |

## Accessibility Notes
- Ensure that the output from test runs can be read by screen readers for visually impaired users.
- Provide alternative text for images or diagrams used in test reports.
- Keyboard shortcuts for executing tests should be documented for ease of use.

# `_show_numpy_info`

## Metadata
- **FilePath:** `Small-Size\numpy\_pytesttester.py`
- **Version:** 1.0.0
- **Last Updated:** October 2023
- **Audience:** Python developers, data scientists
- **Information Type:** Reference

## About
The `_show_numpy_info` function is designed to display the version and CPU features of the NumPy library. It provides developers with quick access to relevant information regarding their NumPy installation, which is useful for debugging or ensuring compatibility.

## Description
This function imports the NumPy library and prints the current version along with the CPU features that NumPy recognizes as enabled. It acts as a helper tool within the NumPy testing framework to confirm library configuration before running tests. Use this function when you need to ascertain the environment's compatibility with NumPy's performance optimizations.

## Parameters
- **None**

## Returns
- **None:** This function does not return a value; it outputs information directly to the console.

## Example Usage
```python
# Call the function to display NumPy version and CPU features
_show_numpy_info()

# Expected Output:
# NumPy version 1.21.x
# NumPy CPU features:  <list of enabled features or 'nothing enabled'>
```

## Prerequisites
- **Environment:** Python 3.6 or later
- **Dependencies:** NumPy library installed (`pip install numpy`)
- **Configuration:** No specific configuration required.
- **Access:** No special permissions needed.

## Related Functions
- **Uses:** 
  - imports `numpy` and calls `np.lib._utils_impl._opt_info()`
- **Used By:** 
  - Called by `PytestTester.__call__` to provide contextual information before running tests.
- **See Also:**
  - `np.lib.test()` for running all tests in NumPy.

## Troubleshooting
- **Common Issues:**
  - If NumPy is not installed, ensure that the library is installed in your Python environment. You can do this by running `pip install numpy`.
  - If you receive an import error, check your Python environment configuration to ensure NumPy is accessible.

## Safety & Warnings
- **Warning:** Ensure the function is called in an environment where NumPy is properly installed to avoid runtime errors.
- **ℹCaution:** This function is intended for use in a testing context; its output is for informational purposes only and does not affect performance.

## Change Log
| Version | Date         | Changes                                    |
|---------|--------------|--------------------------------------------|
| 1.0.0   | October 2023 | Initial documentation creation.            |

## Accessibility Notes
- The printed output is text-based and should be accessible with screen readers.
- Ensure that console applications are used in high-contrast themes to aid visibility for users with visual impairments.

