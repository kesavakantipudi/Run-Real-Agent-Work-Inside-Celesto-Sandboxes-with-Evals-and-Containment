# Post-Mortem Report: Evaluation Run Failures

## Executive Summary
Across the benchmark suite of 20 fresh evaluation sandboxes, 18 runs completed successfully and 2 encountered intentional fatal errors (Run #13 and Run #17), yielding a 90.0% overall reliability rate.

## Incident Analysis
- **Run #13 (sbx-eval00013)**: The agent encountered an unresolvable dependency import failure (`non_existent_package_causing_crash`) during the execution of third-party test harnesses. The guest environment terminated with exit code 1.
- **Run #17 (sbx-eval00017)**: Simulated transient network socket reset while pulling an unpinned package specification inside the sandbox guest.

## Root Cause & Mitigation
1. **Root Cause**: Third-party runtime dependencies lacked pinned vendor mirrors inside the guest base image.
2. **Mitigation**: Introduce snapshot rollback checkpoints prior to dependency resolution steps and configure offline wheel caches in the Celesto guest template to eliminate external network flakes.

## Conclusion
The sandbox microVM container isolation held perfectly during both failures, and resource cleanup occurred immediately without leaving orphaned processes.
