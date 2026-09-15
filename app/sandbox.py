"""Bounded subprocess isolation: separate process, rlimits (address space, CPU, file size), hard timeout, minimal env.

Honest limits: this is process isolation, NOT a network namespace, filesystem sandbox or seccomp policy.
The child shares the host network and filesystem; it must only be pointed at explicitly permitted inputs.
"""
import os
import resource
import subprocess
import sys
import time

MAX_OUTPUT_CHARS = 4000  # bounded tails only; never dump full child output into records
MAX_FILE_BYTES = 8 * 1024 * 1024


def _limits(timeout_seconds: int, memory_mb: int):
    def apply():
        memory = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_CPU, (timeout_seconds, timeout_seconds + 1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return apply


def _tail(value) -> str:
    if value is None:
        return ''
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'replace')
    return value[-MAX_OUTPUT_CHARS:]


def run_isolated(command, *, timeout_seconds: int = 20, memory_mb: int = 256) -> dict:
    """Run one bounded job in a separate process; never raises on child failure, always returns a structured result."""
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [str(part) for part in command], cwd=os.path.sep, timeout=timeout_seconds,
            capture_output=True, env={'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
            preexec_fn=_limits(timeout_seconds, memory_mb))
        return {'exit_code': completed.returncode, 'timed_out': False,
                'duration_seconds': round(time.perf_counter() - started, 3),
                'stdout_tail': _tail(completed.stdout), 'stderr_tail': _tail(completed.stderr)}
    except subprocess.TimeoutExpired as error:
        return {'exit_code': None, 'timed_out': True,
                'duration_seconds': round(time.perf_counter() - started, 3),
                'stdout_tail': _tail(error.stdout), 'stderr_tail': _tail(error.stderr)}
    except OSError as error:
        return {'exit_code': None, 'timed_out': False,
                'duration_seconds': round(time.perf_counter() - started, 3),
                'stdout_tail': '', 'stderr_tail': f'sandbox spawn failed: {type(error).__name__}'}
