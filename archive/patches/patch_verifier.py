import re

with open('src/sovereign/core/coding/verifier.py', 'r') as f:
    content = f.read()

# Replace verify_submission implementation
new_verify = '''    @classmethod
    def verify_submission(
        cls,
        code: str,
        task_goal: str,
        workspace: TaskWorkspace,
        boundary: ExecutionBoundary,
        timeout_seconds: float = 10.0,
        trusted_tests: Optional[str] = None
    ) -> TrustedVerificationReport:
        """
        Independently verifies generated code in the task workspace.
        """
        # PHASE 1 & 2: Trust Boundary and Spoofing Prevention
        # The current MVP ExecutionBoundary runs natively on the host OS (DEGRADED mode) and lacks sandboxing.
        # Because submitted code and the test harness execute in the same Python process, the submitted code
        # can patch built-ins, read the harness source, or overwrite any file/stdout marker.
        # We cannot guarantee a genuinely separate trusted result channel. We explicitly document this limitation
        # and fail closed rather than faking security with unpredictable markers.
        if boundary.security_mode.value == "DEGRADED" or boundary.security_mode.value == "degraded":
            return TrustedVerificationReport(
                status=CodeVerificationStatus.VERIFICATION_INCONCLUSIVE,
                failure_reason="ExecutionBoundary lacks OS-level isolation (DEGRADED mode). A secure trusted result channel cannot be guaranteed, making verification spoofable. Workflow failed closed."
            )

        # PHASE 3: Test Provenance
        # If no explicitly supplied trusted tests are provided by the application, we must fail closed.
        # We no longer execute arbitrary model-generated test_ functions (legacy Case C), as that violates provenance.
        if not trusted_tests:
            return TrustedVerificationReport(
                status=CodeVerificationStatus.VERIFICATION_INCONCLUSIVE,
                failure_reason="No explicit trusted test specification provided by the application."
            )

        # (Unreachable in MVP since mode is DEGRADED)
        return TrustedVerificationReport(
            status=CodeVerificationStatus.VERIFICATION_INCONCLUSIVE,
            failure_reason="Unreachable in current architecture."
        )

    @classmethod
    def _build_test_harness(cls, code: str, goal_lower: str, report_marker: str, trusted_tests: Optional[str] = None) -> Optional[str]:
        # Legacy harness logic removed because it cannot be securely executed in this architecture.
        return None
'''

# Use regex to replace everything from     @classmethod\n    def verify_submission( to the end of the file.
match = re.search(r'    @classmethod\n    def verify_submission\(', content)
if match:
    clean_content = content[:match.start()] + new_verify
    with open('src/sovereign/core/coding/verifier.py', 'w') as f:
        f.write(clean_content)
