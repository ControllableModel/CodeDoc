# `PytestTester.__init__`

## Metadata
- **File Path:** `Small-Size\numpy\_pytesttester.py`
- **Version:** 1.0.0
- **Last Updated:** 2023-10-01
- **Audience:** Developers using the NumPy testing framework
- **Information Type:** Reference

## About
The `PytestTester.__init__` function initializes an instance of the `PytestTester` class with a specified module name. This is crucial for configuring testing environments within the NumPy framework.

## Description
The `__init__` method sets up the `PytestTester` instance by accepting a `module_name` parameter. This parameter is assigned to both the instance's `module_name` attribute and the private `__module__` attribute, allowing the testing utilities to reference the correct module when executing tests.

## Parameters
| Name         | Type   | Description                                            | Defaults | Constraints |
|--------------|--------|--------------------------------------------------------|----------|-------------|
| `module_name`| string | The name of the module that this tester will handle. | None     | Must be a valid module name. |

## Returns
- **None**: This constructor does not return a value. It initializes the instance of `PytestTester`.

## Example Usage
```python
# Initializing a PytestTester instance for the 'my_module' module
from numpy.pytesttester import PytestTester

# Create an instance of PytestTester
tester = PytestTester(module_name='my_module')

# At this point, tester is ready to perform tests on 'my_module'
```

## Prerequisites
- **Environment:** 
  - Python 3.6 or higher
  - Compatible with Unix and Windows operating systems
- **Dependencies:** 
  - NumPy must be installed. 
- **Configuration:**
  - Ensure that the target module is accessible in the testing environment.
- **Access:** 
  - Typical read access permissions are required for the target module's files.

## Related Functions
- **Uses:** 
  - No functions called directly within the constructor.
- **Used By:** 
  - `PytestTester.run_tests()` may utilize the initialized instance to execute tests on the specified module.
- **See Also:** 
  - `PytestTester` class documentation for additional methods and usage.

## Troubleshooting
- **Issue:** If the module specified does not exist, a `ModuleNotFoundError` will be raised when attempting to run tests.
  - **Solution:** Ensure the `module_name` provided is correct and that the module is properly installed and accessible.

## Safety & Warnings
- **Warning:** Be cautious about the module name provided as an argument; an incorrect name can result in runtime errors.
- **ℹCaution:** Always ensure that the module is properly defined before running tests to avoid failures.
- **Note:** This constructor does not perform any validations on the module name, so developers should ensure its correctness.

## Change Log
| Version | Date       | Changes                        |
|---------|------------|--------------------------------|
| 1.0.0   | 2023-10-01 | Initial release of documentation. |

## Accessibility Notes
- Accessible to users familiar with Python programming concepts.
- Text descriptions and parameter explanations are concise and designed for easy comprehension.
- The usage example includes clear comments to enhance understanding for all user levels.

# `PytestTester.__call__`

## Metadata
- **FilePath:** `Small-Size\numpy\_pytesttester.py`
- **Version:** 1.0.0
- **Last Updated:** October 2023
- **Audience:** Developers using the NumPy library for testing
- **Information Type:** Procedural / Reference

## About
The `__call__` method of the `PytestTester` class allows users to execute tests for a specific module using the pytest framework, facilitating the validation of NumPy code through various testing configurations.

## Description
This method is designed to encapsulate pytest's execution in a user-friendly manner. It provides flexibility in terms of which tests to run (fast or full), output verbosity, and additional pytest command-line arguments. Users can specify test coverage and duration reporting, allowing them to tailor their testing approach based on different testing needs.

## Parameters
- **label**: `str`, optional
  - Test selection mode; accepts values:
    - `'fast'`: skips tests marked as `pytest.mark.slow`.
    - `'full'`: runs all tests without exclusions.
  - Default is `'fast'`.

- **verbose**: `int`, optional
  - Controls the level of detail in test output. 
  - Range: 1 (default) to 3, with higher values providing more detailed output.

- **extra_argv**: `list`, optional
  - List of additional arguments to pass to pytest.

- **doctests**: `bool`, optional
  - Not supported. Default: `False`.

- **coverage**: `bool`, optional
  - If `True`, enables reporting code coverage for NumPy. Default: `False`.
  - Requires installation of `pytest-cov`.

- **durations**: `int`, optional
  - Determines reporting on test duration:
    - `< 0`: do nothing.
    - `0`: report duration for all tests.
    - `> 0`: report time for the slowest tests.
  - Default is `-1`.

- **tests**: `test` or `list of tests`, optional
  - Specifies which tests to execute. If `None`, executes all tests in the module.

## Returns
- **result**: `bool`
  - Returns `True` if tests executed successfully, `False` otherwise.

## Example Usage
```python
import numpy as np

# Create an instance of PytestTester
tester = PytestTester()

# Run tests with default parameters
result = tester(label='fast', verbose=2, coverage=True)

# Output the result of the test run
print(f"Test run {'succeeded' if result else 'failed'}.")

# Expected output could look something like:
# Test run succeeded.
```

## Prerequisites
- **Environment:** Python 3.6 or later, any OS that supports Python.
- **Dependencies:** Install pytest and pytest-cov using:
  ```bash
  pip install pytest pytest-cov
  ```
- **Configuration:** Ensure pytest is configured according to specific project requirements.
- **Access:** User needs sufficient permissions to execute tests on the intended module.

## Related Functions
- **Uses:** 
  - Calls `pytest.main()` to execute the test commands.
  
- **Used By:** 
  - Typically invoked through the `test` interface of NumPy modules, e.g., `np.lib.test()`.

- **See Also:** 
  - Refer to `pytest` documentation for additional command-line options and features.

## Troubleshooting
- **Common Issues:**
  - If tests do not run as expected:
    - Ensure that the correct module is being tested.
    - Check for any required dependencies not installed.
  - For coverage to be reported, verify that `pytest-cov` is installed correctly.

- **Error Codes:**
  - A non-zero exit code from pytest indicates failures in test execution.

## Safety & Warnings
- **Warning:** Ensure that tests are run in a safe, controlled environment to prevent unintended modifications to production data.
- **ℹCaution:** Review test outputs carefully to identify failing tests that may affect functionality.

## Change Log
| Version | Date        | Changes               |
|---------|-------------|-----------------------|
| 1.0.0   | October 2023| Initial release.      |

## Accessibility Notes
- The method is designed to be used in a standard Python environment, and is compatible with screen readers. Ensure clear output in the console to support visually impaired users.

# `_show_numpy_info`

## Metadata
- **FilePath:** `Small-Size\numpy\_pytesttester.py`
- **Version:** 1.0.0
- **Last Updated:** October 2023
- **Audience:** Python developers working with NumPy
- **Information Type:** Reference

## About
The `_show_numpy_info` function provides basic information about the NumPy library's version and CPU features. It is useful for debugging and understanding the environment setup for applications that depend on NumPy.

## Description
The `_show_numpy_info` function imports the NumPy library and prints the current version of NumPy along with its enabled CPU features. This function is particularly useful in scenarios where developers need to verify the installed version and capabilities of NumPy in their working environment.

## Parameters
- **None**

## Returns
- **None**: The function does not return a value; it outputs information directly to the console.

## Example Usage
```python
# Example of calling the _show_numpy_info function
_show_numpy_info()

# Expected output:
# NumPy version 1.21.2
# NumPy CPU features:  AVX2, AVX, FMA
```

## Prerequisites
- **Environment:** Python 3.6 or higher, compatible with NumPy.
- **Dependencies:** NumPy library must be installed. Install it using `pip install numpy`.
- **Configuration:** None required; ensure the working environment has access to the NumPy library.
- **Access:** No special permissions are needed to execute this function in standard development environments.

## Related Functions
- **Uses:** `_show_numpy_info` calls `np.__version__` and `np.lib._utils_impl._opt_info()`.
- **Used By:** This function could be integrated into larger testing or debugging frameworks to automatically verify library configurations.
- **See Also:** 
  - `[numpy.__version__](https://numpy.org/doc/stable/reference/constants.html#numpy.__version__)` - A constant that gives the version of NumPy.
  - `[np.lib._utils_impl._opt_info](https://numpy.org/doc/stable/reference/generated/numpy.lib._utils_impl._opt_info.html)` - Provides information about the available CPU features.

## Troubleshooting
- **Common Issue:** NumPy not found.
  - **Solution:** Ensure that NumPy is installed correctly in your Python environment. You can install it via `pip install numpy`.
  
- **Common Issue:** No CPU features displayed.
  - **Solution:** Check that your NumPy installation supports optimizations for the hardware. If running in a constrained environment (like some container setups), CPU features may not be available.

## Safety & Warnings
- **Warning:** This function directly accesses internal APIs to fetch CPU features, which may not be stable across NumPy releases. Future changes in NumPy may affect this functionality.
- **ℹCaution:** The availability of certain CPU features depends on the actual hardware and the NumPy version. This should not be relied upon for critical applications without validation.
- **Note:** Regularly update Python and NumPy to the latest versions for performance and feature improvements.

## Change Log
| Version | Date          | Changes                       |
|---------|---------------|-------------------------------|
| 1.0.0   | October 2023  | Initial documentation created. |

## Accessibility Notes
The output of this function is designed to be easily readable for developers. Ensure that environments running this function support standard output for visibility. The function does not currently include explicit support for screen reader compatibility, as it solely relies on console output.

