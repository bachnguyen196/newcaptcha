#!/usr/bin/env python3
"""
Automated Test Runner for Captcha Security Lab
Executes all unit tests and prints a formatted report.
"""

import sys
import unittest

def run_all_tests():
    # Force UTF-8 on Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("\n" + "=" * 70)
    print("🛡️  CAPTCHA SECURITY LAB - AUTOMATED TEST SUITE")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("📊 TỔNG KẾT KẾT QUẢ KIỂM THỬ")
    print("=" * 70)
    print(f"Tổng số bài test thực hiện : {result.testsRun}")
    print(f"Số bài test THÀNH CÔNG     : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Số bài test THẤT BẠI       : {len(result.failures)}")
    print(f"Số lỗi phát sinh (Errors)  : {len(result.errors)}")
    print("-" * 70)

    if result.wasSuccessful():
        print("✅ TOÀN BỘ BÀI TEST ĐẠT CHUẨN AN TOÀN (100% PASSED)!")
        print("=" * 70 + "\n")
        return 0
    else:
        print("❌ CÓ BÀI TEST THẤT BẠI. VUI LÒNG KIỂM TRA LẠI LOG!")
        print("=" * 70 + "\n")
        return 1

if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
