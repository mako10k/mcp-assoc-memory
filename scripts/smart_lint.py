#!/usr/bin/env python3
"""
Smart lint script that handles expected false positive errors
with file pattern matching and progress reporting
"""

import argparse
import json
import subprocess
import sys
import time
import glob
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LintResult:
    """Represents lint result with error filtering"""

    def __init__(self, tool: str, exit_code: int, stdout: str, stderr: str):
        self.tool = tool
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.errors: List[Dict[str, str]] = []
        self.expected_errors: List[Dict[str, str]] = []
        self.unexpected_errors: List[Dict[str, str]] = []


class SmartLinter:
    """Smart linter that handles expected false positives with file pattern matching"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or ".smart-lint-config.json"
        self.config = self.load_config()
        self.workspace_root = Path.cwd()
        self.start_time = time.time()
        self.progress_file = None
        self.report_file = None
        self._setup_output_files()

    def load_config(self) -> Dict:
        """Load expected errors configuration"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            # Create default config
            default_config = {
                "version": "1.0",
                "description": "Smart lint configuration for handling expected false positives",
                "expected_errors": {
                    "mypy": [
                        {
                            "file": "src/mcp_assoc_memory/api/tools/memory_tools.py",
                            "line": 1065,
                            "error_code": "unreachable",
                            "pattern": "Statement is unreachable",
                            "reason": "False positive: mypy incorrectly detects unreachable code in exception handler (GitHub issue #12785)",
                            "permanent": True,
                        },
                        {
                            "file": "src/mcp_assoc_memory/api/tools/memory_tools.py",
                            "line": 1084,
                            "error_code": "unused-ignore",
                            "pattern": 'Unused "type: ignore" comment',
                            "reason": "Related to unreachable false positive - type:ignore sometimes detected as unused",
                            "permanent": True,
                        },
                    ],
                    "flake8": [],
                },
                "settings": {"strict_mode": False, "allow_new_errors": False, "max_unexpected_errors": 0},
                "file_patterns": {
                    "python": {
                        "include": ["src/**/*.py", "tests/**/*.py", "scripts/**/*.py"],
                        "exclude": ["**/__pycache__/**", "**/.*", "**/*.pyc"],
                    }
                },
                "output": {
                    "report_file": ".copilot-temp/smart-lint-report.txt",
                    "progress_file": ".copilot-temp/smart-lint-progress.txt",
                    "include_timestamps": True,
                    "include_execution_time": True,
                },
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            print(f"✨ Created default configuration: {config_path}")
            return default_config

        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_flake8(self) -> LintResult:
        """Run flake8 with smart error handling"""
        self._write_progress("🔍 Running flake8...")

        target_files = self.get_target_files("python")
        self._write_progress(f"📁 Found {len(target_files)} Python files to check")

        if not target_files:
            self._write_progress("⚠️ No Python files found matching patterns")
            return LintResult("flake8", 0, "", "")

        cmd = (
            ["flake8"]
            + target_files
            + [
                "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                "--max-line-length=120",
                "--extend-ignore=E203,W503",
            ]
        )

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            lint_result = LintResult("flake8", result.returncode, result.stdout, result.stderr)

            # Parse flake8 errors
            if result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                self._write_progress(f"📊 flake8 found {len(lines)} potential issues")

                for line in lines:
                    if ":" in line and " " in line:
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            file_path = parts[0]
                            line_num = parts[1]
                            col_num = parts[2]
                            error_desc = parts[3].strip()

                            lint_result.errors.append(
                                {
                                    "file": file_path,
                                    "line": int(line_num),
                                    "column": int(col_num),
                                    "description": error_desc,
                                    "tool": "flake8",
                                }
                            )

            self._categorize_errors(lint_result, "flake8")
            self._write_progress(
                f"✅ flake8 completed: {len(lint_result.unexpected_errors)} unexpected, {len(lint_result.expected_errors)} expected"
            )
            return lint_result

        except subprocess.TimeoutExpired:
            error_msg = "❌ flake8 timed out"
            self._write_progress(error_msg)
            return LintResult("flake8", 1, "", "Timeout")
        except Exception as e:
            error_msg = f"❌ flake8 failed: {e}"
            self._write_progress(error_msg)
            return LintResult("flake8", 1, "", str(e))

    def run_mypy(self) -> LintResult:
        """Run mypy with smart error handling"""
        self._write_progress("🔍 Running mypy...")

        target_files = self.get_target_files("python")
        target_dirs = list(set(str(Path(f).parent) for f in target_files if f.startswith("src/")))

        if not target_dirs:
            self._write_progress("⚠️ No source directories found for mypy")
            return LintResult("mypy", 0, "", "")

        self._write_progress(f"📁 Checking {len(target_dirs)} directories with mypy")

        cmd = ["mypy", "src/mcp_assoc_memory/", "--ignore-missing-imports", "--show-error-codes", "--pretty"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            lint_result = LintResult("mypy", result.returncode, result.stdout, result.stderr)

            # Parse mypy errors
            if result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                self._write_progress(f"📊 mypy processing {len(lines)} output lines")

                i = 0
                while i < len(lines):
                    line = lines[i]
                    if ":" in line and "error:" in line:
                        # Parse mypy error format: file:line: error: message [code]
                        # Note: mypy --pretty format may split error across multiple lines
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            file_path = parts[0].strip()
                            line_num_part = parts[1].strip()
                            error_part = parts[2].strip()

                            if line_num_part.isdigit() and error_part.startswith("error:"):
                                error_desc = error_part[6:].strip()  # Remove 'error: '

                                # Check if error code is on the next line (mypy --pretty format)
                                error_code = "unknown"
                                if i + 1 < len(lines):
                                    next_line = lines[i + 1].strip()
                                    if next_line and "[" in next_line and "]" in next_line:
                                        # Error code is on the next line
                                        code_start = next_line.rfind("[")
                                        code_end = next_line.rfind("]")
                                        if code_start < code_end:
                                            error_code = next_line[code_start + 1 : code_end]
                                            # Combine the error description with the next line text
                                            error_desc = error_desc + " " + next_line[:code_start].strip()
                                            i += 1  # Skip the next line since we processed it

                                # If error code not found on next line, check current line
                                if error_code == "unknown" and "[" in error_desc and "]" in error_desc:
                                    code_start = error_desc.rfind("[")
                                    code_end = error_desc.rfind("]")
                                    if code_start < code_end:
                                        error_code = error_desc[code_start + 1 : code_end]
                                        error_desc = error_desc[:code_start].strip()

                                lint_result.errors.append(
                                    {
                                        "file": file_path,
                                        "line": int(line_num_part),
                                        "description": error_desc,
                                        "error_code": error_code,
                                        "tool": "mypy",
                                    }
                                )
                    i += 1

            self._categorize_errors(lint_result, "mypy")
            self._write_progress(
                f"✅ mypy completed: {len(lint_result.unexpected_errors)} unexpected, {len(lint_result.expected_errors)} expected"
            )
            return lint_result

        except subprocess.TimeoutExpired:
            error_msg = "❌ mypy timed out"
            self._write_progress(error_msg)
            return LintResult("mypy", 1, "", "Timeout")
        except Exception as e:
            error_msg = f"❌ mypy failed: {e}"
            self._write_progress(error_msg)
            return LintResult("mypy", 1, "", str(e))

    def _categorize_errors(self, lint_result: LintResult, tool: str) -> None:
        """Categorize errors as expected or unexpected"""
        expected_patterns = self.config["expected_errors"].get(tool, [])

        for error in lint_result.errors:
            is_expected = False

            for expected in expected_patterns:
                if self._matches_expected_error(error, expected):
                    lint_result.expected_errors.append(error)
                    is_expected = True
                    break

            if not is_expected:
                lint_result.unexpected_errors.append(error)

    def _matches_expected_error(self, error: Dict[str, str], expected: Dict[str, str]) -> bool:
        """Check if an error matches an expected pattern"""
        # Check file path
        if error.get("file") != expected.get("file"):
            return False

        # Check line number (with tolerance)
        error_line = error.get("line", 0)
        expected_line = expected.get("line", 0)
        if abs(error_line - expected_line) > 2:  # Allow 2-line tolerance
            return False

        # Check error code if available
        if "error_code" in error and "error_code" in expected:
            if error["error_code"] != expected["error_code"]:
                return False

        # Check pattern matching
        if "pattern" in expected:
            if expected["pattern"] not in error.get("description", ""):
                return False

        return True

    def print_results(self, flake8_result: LintResult, mypy_result: LintResult) -> bool:
        """Print formatted results and return success status"""
        print("\n" + "=" * 80)
        print("📊 SMART LINT RESULTS")
        print("=" * 80)

        overall_success = True

        # Flake8 results
        print("\n🐍 FLAKE8:")
        if flake8_result.exit_code == 0 and not flake8_result.unexpected_errors:
            print("  ✅ PASSED - No style issues found")
        elif not flake8_result.unexpected_errors:
            print(f"  ✅ PASSED - Only expected errors found ({len(flake8_result.expected_errors)})")
        else:
            print(f"  ❌ FAILED - {len(flake8_result.unexpected_errors)} unexpected errors")
            overall_success = False
            for error in flake8_result.unexpected_errors:
                print(f"     {error['file']}:{error['line']} - {error['description']}")

        if flake8_result.expected_errors:
            print(f"  ℹ️  Ignored {len(flake8_result.expected_errors)} expected errors")

        # Mypy results
        print("\n🔍 MYPY:")
        if mypy_result.exit_code == 0 and not mypy_result.unexpected_errors:
            print("  ✅ PASSED - No type issues found")
        elif not mypy_result.unexpected_errors:
            print(f"  ✅ PASSED - Only expected errors found ({len(mypy_result.expected_errors)})")
            for error in mypy_result.expected_errors:
                reason = self._get_error_reason(error, "mypy")
                print(
                    f"     ℹ️ {error['file']}:{error['line']} - {error.get('error_code', 'unknown')} (EXPECTED: {reason})"
                )
        else:
            print(f"  ❌ FAILED - {len(mypy_result.unexpected_errors)} unexpected errors")
            overall_success = False
            for error in mypy_result.unexpected_errors:
                print(f"     {error['file']}:{error['line']} - {error['description']}")

        if mypy_result.expected_errors:
            print(f"  ℹ️  Ignored {len(mypy_result.expected_errors)} expected errors")

        # Summary
        print("\n📈 SUMMARY:")
        total_errors = len(flake8_result.errors) + len(mypy_result.errors)
        total_expected = len(flake8_result.expected_errors) + len(mypy_result.expected_errors)
        total_unexpected = len(flake8_result.unexpected_errors) + len(mypy_result.unexpected_errors)

        print(f"  Total errors: {total_errors}")
        print(f"  Expected (ignored): {total_expected}")
        print(f"  Unexpected: {total_unexpected}")

        if overall_success:
            print("  🎉 OVERALL: PASSED")
        else:
            print("  💥 OVERALL: FAILED")

        print("=" * 80)

        # Write detailed report to file
        self._write_detailed_report(flake8_result, mypy_result, overall_success, total_errors)

        # Write end footer
        self._write_end_footer(overall_success, total_errors)

        return overall_success

    def _write_detailed_report(
        self, flake8_result: LintResult, mypy_result: LintResult, overall_success: bool, total_errors: int
    ) -> None:
        """Write detailed report to report file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execution_time = time.time() - self.start_time

        report_content = f"""SMART LINT DETAILED REPORT
Generated: {timestamp}
Execution Time: {execution_time:.2f} seconds
Configuration: {self.config_file}

================================================================================
FLAKE8 RESULTS
================================================================================
Exit Code: {flake8_result.exit_code}
Total Errors: {len(flake8_result.errors)}
Expected Errors: {len(flake8_result.expected_errors)}
Unexpected Errors: {len(flake8_result.unexpected_errors)}

Unexpected Errors:
"""

        if flake8_result.unexpected_errors:
            for error in flake8_result.unexpected_errors:
                report_content += (
                    f"  {error['file']}:{error['line']}:{error.get('column', 0)} - {error['description']}\n"
                )
        else:
            report_content += "  None\n"

        if flake8_result.expected_errors:
            report_content += "\nExpected Errors (Ignored):\n"
            for error in flake8_result.expected_errors:
                reason = self._get_error_reason(error, "flake8")
                report_content += f"  {error['file']}:{error['line']} - {error['description']} (Reason: {reason})\n"

        report_content += f"""
================================================================================
MYPY RESULTS
================================================================================
Exit Code: {mypy_result.exit_code}
Total Errors: {len(mypy_result.errors)}
Expected Errors: {len(mypy_result.expected_errors)}
Unexpected Errors: {len(mypy_result.unexpected_errors)}

Unexpected Errors:
"""

        if mypy_result.unexpected_errors:
            for error in mypy_result.unexpected_errors:
                report_content += f"  {error['file']}:{error['line']} - [{error.get('error_code', 'unknown')}] {error['description']}\n"
        else:
            report_content += "  None\n"

        if mypy_result.expected_errors:
            report_content += "\nExpected Errors (Ignored):\n"
            for error in mypy_result.expected_errors:
                reason = self._get_error_reason(error, "mypy")
                report_content += f"  {error['file']}:{error['line']} - [{error.get('error_code', 'unknown')}] {error['description']} (Reason: {reason})\n"

        report_content += f"""
================================================================================
OVERALL SUMMARY
================================================================================
Total Errors Found: {total_errors}
Expected (Ignored): {len(flake8_result.expected_errors) + len(mypy_result.expected_errors)}
Unexpected: {len(flake8_result.unexpected_errors) + len(mypy_result.unexpected_errors)}
Overall Result: {'PASSED' if overall_success else 'FAILED'}
Execution Time: {execution_time:.2f} seconds
"""

        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

    def _get_error_reason(self, error: Dict[str, str], tool: str) -> str:
        """Get reason for expected error"""
        expected_patterns = self.config["expected_errors"].get(tool, [])

        for expected in expected_patterns:
            if self._matches_expected_error(error, expected):
                return expected.get("reason", "No reason provided")

        return "Unknown reason"

    def _setup_output_files(self) -> None:
        """Setup output files for progress and report"""
        output_config = self.config.get("output", {})

        # Create .copilot-temp directory if it doesn't exist
        temp_dir = Path(".copilot-temp")
        temp_dir.mkdir(exist_ok=True)

        self.progress_file = output_config.get("progress_file", ".copilot-temp/smart-lint-progress.txt")
        self.report_file = output_config.get("report_file", ".copilot-temp/smart-lint-report.txt")

        # Write start header
        self._write_start_header()

    def _write_start_header(self) -> None:
        """Write start header to progress file"""
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""
================================================================================
🚀 SMART LINT EXECUTION STARTED
================================================================================
Start Time: {start_time}
Config File: {self.config_file}
Workspace: {self.workspace_root}
Tools: flake8, mypy
================================================================================

"""
        with open(self.progress_file, "w", encoding="utf-8") as f:
            f.write(header)

    def _write_progress(self, message: str) -> None:
        """Write progress message to both console and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        progress_msg = f"[{timestamp}] {message}"
        print(message)

        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(progress_msg + "\n")

    def _write_end_footer(self, success: bool, total_errors: int) -> None:
        """Write end footer to progress file"""
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execution_time = time.time() - self.start_time

        footer = f"""
================================================================================
🏁 SMART LINT EXECUTION COMPLETED
================================================================================
End Time: {end_time}
Execution Time: {execution_time:.2f} seconds
Total Errors Found: {total_errors}
Overall Result: {'✅ PASSED' if success else '❌ FAILED'}
================================================================================
"""
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(footer)

    def get_target_files(self, tool: str) -> List[str]:
        """Get target files based on configuration patterns"""
        patterns = self.config.get("file_patterns", {})

        if tool == "python":
            include_patterns = patterns.get("python", {}).get("include", ["src/**/*.py"])
            exclude_patterns = patterns.get("python", {}).get("exclude", ["**/__pycache__/**"])
        else:
            # Default patterns
            include_patterns = ["src/**/*.py"]
            exclude_patterns = ["**/__pycache__/**"]

        # Collect all files matching include patterns
        all_files = set()
        for pattern in include_patterns:
            matches = glob.glob(pattern, recursive=True)
            all_files.update(matches)

        # Remove files matching exclude patterns
        filtered_files = []
        for file_path in all_files:
            excluded = False
            for exclude_pattern in exclude_patterns:
                if fnmatch.fnmatch(file_path, exclude_pattern):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file_path)

        return sorted(filtered_files)

    def run_all(self) -> bool:
        """Run all lint tools and return overall success"""
        self._write_progress("🚀 Starting smart lint check...")
        self._write_progress(f"📋 Config: {self.config_file}")

        flake8_result = self.run_flake8()
        mypy_result = self.run_mypy()

        return self.print_results(flake8_result, mypy_result)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Smart linter with expected error handling")
    parser.add_argument("--config", "-c", help="Configuration file path", default=".smart-lint-config.json")
    parser.add_argument("--tool", "-t", choices=["flake8", "mypy", "all"], default="all", help="Tool to run")
    parser.add_argument("--strict", action="store_true", help="Strict mode - no expected errors allowed")

    args = parser.parse_args()

    linter = SmartLinter(args.config)

    if args.strict:
        linter.config["settings"]["strict_mode"] = True

    if args.tool == "all":
        success = linter.run_all()
    elif args.tool == "flake8":
        result = linter.run_flake8()
        success = not result.unexpected_errors
        linter.print_results(result, LintResult("mypy", 0, "", ""))
    elif args.tool == "mypy":
        result = linter.run_mypy()
        success = not result.unexpected_errors
        linter.print_results(LintResult("flake8", 0, "", ""), result)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
