# Post-Mortem Report: Evaluation Run Failures

## Executive Summary
Across the benchmark suite of 20 fresh evaluation sandboxes, 18 runs completed successfully and 2 encountered intentional fatal errors (Run #13 and Run #17), yielding a 90.0% overall reliability rate.

## Incident Analysis
- **Run #13 (sbx-eval00013)**: The agent encountered an unresolvable command execution failure (`command_that_does_not_exist_in_guest`) during the integration test execution phase. The guest environment terminated with exit code 127.
- **Run #17 (sbx-eval00017)**: Simulated transient failure while attempting to execute an unverified binary inside the sandbox guest.

## Root Cause & Mitigation
1. **Root Cause**: Third-party runtime binaries were not present in the default scratch microVM image.
2. **Mitigation**: Introduce snapshot rollback checkpoints prior to dependency execution steps and pre-bake required packages into custom Celesto guest templates.

## Conclusion
The sandbox microVM container isolation held perfectly during both failures, and resource cleanup occurred immediately without leaving orphaned cloud computers or burning credits.
