"""
自动化回归测试 - 测试框架
简单实现:测试发现、覆盖率、CI集成
"""
import pytest
from pathlib import Path

def discover_tests():
    """发现所有测试"""
    test_files = list(Path("tests").rglob("test_*.py"))
    return test_files

def run_tests_with_coverage():
    """运行测试并生成覆盖率报告"""
    import subprocess
    subprocess.run(["pytest", "--cov=agents", "--cov-report=html", "tests/"])

# 快速实现
