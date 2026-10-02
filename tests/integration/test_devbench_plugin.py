pytest_plugins = ["pytester"]


def test_mo2_suite_is_opt_in_before_connection(pytester):
    pytester.makeconftest("""
import mopk.devbench.pytest_plugin as plugin
pytest_plugins = ["mopk.devbench.pytest_plugin"]
def forbidden(*args, **kwargs):
    raise AssertionError("Connection attempted without opt-in")
plugin.find_instance = forbidden
plugin.Client = forbidden
""")
    pytester.makepyfile("""
import pytest
@pytest.mark.mo2
def test_mo2(devbench):
    raise AssertionError("MO2 test ran without opt-in")
""")
    pytester.runpytest_subprocess("-q").assert_outcomes(skipped=1)
