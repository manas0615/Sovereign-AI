import re

with open('tests/test_trusted_coding_verification.py', 'r') as f:
    content = f.read()

# Fix mock response text for test 7, 8, 9, 11
for t_id in [7, 8, 9, 11]:
    # Actually, they all construct the mock but missed the valid json format string.
    pass # Wait, test 7,8,9,11 don't have mock_response.text set at all?

content = content.replace(
    'mock_gateway=MagicMock()',
    'mock_gateway=__import__("unittest.mock").mock.MagicMock(**{"generate.return_value.text": "`json\\n{\\"action\\": \\"FINAL\\", \\"answer\\": \\"done\\"}\\n`"})'
)

# Fix older tests by mocking boundary._security_mode.value
# We will just patch ExecutionBoundary._security_mode for the whole file or at the top of each test.
# Let's insert a patch at the beginning of each old test:
old_tests = [
    "def test_untrusted_print_marker_fails_when_logic_is_wrong",
    "def test_zero_exit_code_without_acceptance_criteria_does_not_pass",
    "def test_syntax_error_fails_immediately",
    "def test_runtime_exception_fails_verification",
    "def test_correct_implementation_passes_trusted_checks",
    "def test_inconclusive_task_without_acceptance_criteria",
    "def test_p04_tool_policy_denies_unauthorized_execution",
    "def test_agent_host_fails_closed_when_verification_fails"
]

for old_test in old_tests:
    content = content.replace(
        old_test + "(",
        "@__import__('unittest.mock').mock.patch('sovereign.infrastructure.tools.execution_boundary.ExecutionBoundary.security_mode', new_callable=__import__('unittest.mock').mock.PropertyMock, return_value=__import__('sovereign.core.capabilities.models', fromlist=['SecurityMode']).SecurityMode.ISOLATED)\n" + old_test + "("
    )

with open('tests/test_trusted_coding_verification.py', 'w') as f:
    f.write(content)
