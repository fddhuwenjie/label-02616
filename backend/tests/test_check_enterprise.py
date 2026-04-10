#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业信息核查工具单元测试
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_enterprise import EnterpriseChecker, EnterpriseCheckerError


class TestEnterpriseChecker:
    """企业信息检查器单元测试"""

    def setup_method(self):
        """测试初始化"""
        self.checker = EnterpriseChecker(base_path="/tmp")

    def test_check_business_status_normal_should_pass(self):
        """测试check_business_status：营业状态正常返回通过"""
        row = pd.Series({'登记状态': '在营（开业）'})
        is_valid, msg = self.checker.check_business_status(row)
        assert is_valid is True
        assert "登记状态: 在营（开业）" in msg
        assert "[异常]" not in msg

    def test_check_business_status_revoked_should_fail(self):
        """测试check_business_status：吊销/注销状态返回异常"""
        row = pd.Series({'登记状态': '吊销'})
        is_valid, msg = self.checker.check_business_status(row)
        assert is_valid is False
        assert "登记状态: 吊销" in msg
        assert "[异常]" in msg

    def test_check_business_status_cancelled_should_fail(self):
        """测试check_business_status：注销状态返回异常"""
        row = pd.Series({'登记状态': '注销'})
        is_valid, msg = self.checker.check_business_status(row)
        assert is_valid is False
        assert "[异常]" in msg

    def test_check_business_period_valid_should_pass(self):
        """测试check_business_period：营业期限在有效期内返回通过"""
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        row = pd.Series({'营业期限': f"2020-01-01 至 {future_date}"})
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is True
        assert "[有效]" in msg

    def test_check_business_period_expired_should_fail(self):
        """测试check_business_period：已过期返回异常"""
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        row = pd.Series({'营业期限': f"2020-01-01 至 {past_date}"})
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is False
        assert "[已过期]" in msg

    def test_check_business_period_long_term_should_pass(self):
        """测试check_business_period：\"长期\"返回通过"""
        row = pd.Series({'营业期限': '2020-01-01 至 长期'})
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is True
        assert "[长期有效]" in msg

    def test_check_business_period_no_fixed_term_should_pass(self):
        """测试check_business_period：\"无固定期限\"返回通过"""
        row = pd.Series({'营业期限': '无固定期限'})
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is True
        assert "[长期有效]" in msg

    def test_check_lawsuit_count_zero_should_pass(self):
        """测试check_lawsuit_count：涉诉次数为0返回通过"""
        row = pd.Series({'近一年企业作为被告的涉诉次数': '0'})
        is_valid, msg = self.checker.check_lawsuit_count(row)
        assert is_valid is True
        assert "[异常]" not in msg

    def test_check_lawsuit_count_zero_int_should_pass(self):
        """测试check_lawsuit_count：涉诉次数数字0返回通过"""
        row = pd.Series({'近一年企业作为被告的涉诉次数': 0})
        is_valid, msg = self.checker.check_lawsuit_count(row)
        assert is_valid is True

    def test_check_lawsuit_count_over_threshold_should_fail(self):
        """测试check_lawsuit_count：超过阈值返回异常"""
        row = pd.Series({'近一年企业作为被告的涉诉次数': '3次'})
        is_valid, msg = self.checker.check_lawsuit_count(row)
        assert is_valid is False
        assert "[异常]" in msg

    def test_check_lawsuit_count_nonzero_int_should_fail(self):
        """测试check_lawsuit_count：涉诉次数数字非0返回异常"""
        row = pd.Series({'近一年企业作为被告的涉诉次数': 5})
        is_valid, msg = self.checker.check_lawsuit_count(row)
        assert is_valid is False

    def test_compare_with_previous_no_change_should_return_unchanged(self):
        """测试compare_with_previous：当前数据与上期一致返回无变更"""
        current_row = pd.Series({
            '法定代表人': '张三',
            '经营范围': '计算机技术开发',
            '股东持股占比': '60%',
            '企业地址': '北京市海淀区'
        })
        previous_df = pd.DataFrame([{
            '查询条件': '测试企业',
            '法定代表人': '张三',
            '经营范围': '计算机技术开发',
            '股东持股占比': '60%',
            '企业地址': '北京市海淀区'
        }])
        results = self.checker.compare_with_previous(current_row, previous_df, '测试企业')
        for is_valid, msg in results:
            assert is_valid is True
            assert "未变更" in msg

    def test_compare_with_previous_changed_should_return_details(self):
        """测试compare_with_previous：字段值变化返回变更详情"""
        current_row = pd.Series({
            '法定代表人': '李四',
            '经营范围': '计算机技术开发',
            '股东持股占比': '60%',
            '企业地址': '北京市朝阳区'
        })
        previous_df = pd.DataFrame([{
            '查询条件': '测试企业',
            '法定代表人': '张三',
            '经营范围': '计算机技术开发',
            '股东持股占比': '60%',
            '企业地址': '北京市海淀区'
        }])
        results = self.checker.compare_with_previous(current_row, previous_df, '测试企业')
        changes_found = 0
        for is_valid, msg in results:
            if "已变更" in msg:
                changes_found += 1
                assert "原值:" in msg
                assert "现值:" in msg
        assert changes_found == 2

    @patch('check_enterprise.glob.glob')
    @patch('check_enterprise.os.path.exists')
    @patch('check_enterprise.pd.read_excel')
    def test_run_check_full_process_mock_excel(self, mock_read_excel, mock_exists, mock_glob):
        """测试run_check：完整流程测试，mock Excel文件输入验证输出格式正确"""
        mock_glob.return_value = ['/tmp/企业信息批量查询列表_20250101.xlsx']
        mock_exists.return_value = True
        
        mock_df = pd.DataFrame({
            '查询条件': ['企业A', '企业B'],
            '登记状态': ['在营（开业）', '吊销'],
            '营业期限': ['长期', '2020-01-01 至 2023-01-01'],
            '注销日期': ['无', '2023-06-01'],
            '近一年企业作为被告的涉诉次数': ['0', '5次'],
            '经营异常名单': ['否', '是'],
            '是否安全生产黑名单': ['否', '否'],
            '是否涉金融黑名单': ['否', '否'],
            '是否存在税务行政处罚': ['否', '否'],
            '是否存在公示处罚信息': ['否', '否'],
            '是否存在工商行政处罚': ['否', '否'],
            '是否严重违法失信企业名单': ['否', '否'],
        })
        mock_read_excel.return_value = mock_df

        results = self.checker.run_check(today_date='20250101')
        
        assert len(results) == 2
        
        assert results[0]['enterprise_name'] == '企业A'
        assert results[0]['has_issues'] is False
        assert len(results[0]['checks']) > 0
        
        assert results[1]['enterprise_name'] == '企业B'
        assert results[1]['has_issues'] is True
        
        for result in results:
            assert 'enterprise_name' in result
            assert 'checks' in result
            assert 'has_issues' in result
            for check in result['checks']:
                assert isinstance(check[0], bool)
                assert isinstance(check[1], str)

    def test_validate_columns_missing_columns_should_raise_error(self):
        """测试列验证：缺少必需列应抛出异常"""
        df = pd.DataFrame({'查询条件': ['企业A']})
        with pytest.raises(EnterpriseCheckerError) as exc_info:
            self.checker._validate_columns(df, 'test.xlsx')
        assert "缺少必需的列" in str(exc_info.value)
