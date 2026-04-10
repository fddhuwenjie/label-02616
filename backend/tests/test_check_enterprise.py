#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_enterprise import EnterpriseChecker, EnterpriseCheckerError


class TestEnterpriseChecker:
    def setup_method(self):
        self.checker = EnterpriseChecker(base_path='/tmp')

    def test_check_business_status_normal(self):
        """测试营业状态正常返回通过"""
        data = {'查询条件': '测试企业', '登记状态': '在营（开业）'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_business_status(row)
        assert is_valid is True
        assert '异常' not in msg

    def test_check_business_status_revoked(self):
        """测试吊销状态返回异常"""
        data = {'查询条件': '测试企业', '登记状态': '吊销'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_business_status(row)
        assert is_valid is False
        assert '异常' in msg

    def test_check_business_status_cancelled(self):
        """测试注销状态返回异常"""
        data = {'查询条件': '测试企业', '登记状态': '注销'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_business_status(row)
        assert is_valid is False
        assert '异常' in msg

    def test_check_business_period_valid(self):
        """测试营业期限在有效期内返回通过"""
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        data = {'查询条件': '测试企业', '营业期限': f'2020-01-01 至 {future_date}'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is True
        assert '有效' in msg

    def test_check_business_period_expired(self):
        """测试营业期限已过期返回异常"""
        past_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        data = {'查询条件': '测试企业', '营业期限': f'2020-01-01 至 {past_date}'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is False
        assert '已过期' in msg

    def test_check_business_period_long_term(self):
        """测试营业期限为长期返回通过"""
        data = {'查询条件': '测试企业', '营业期限': '2020-01-01 至 长期'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is True
        assert '长期有效' in msg

    def test_check_business_period_fixed_term(self):
        """测试营业期限为无固定期限返回通过"""
        data = {'查询条件': '测试企业', '营业期限': '无固定期限'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_business_period(row)
        assert is_valid is True
        assert '长期有效' in msg

    def test_check_lawsuit_count_zero(self):
        """测试涉诉次数为0返回通过"""
        data = {'查询条件': '测试企业', '近一年企业作为被告的涉诉次数': '0'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_lawsuit_count(row)
        assert is_valid is True
        assert '异常' not in msg

    def test_check_lawsuit_count_zero_int(self):
        """测试涉诉次数数字0返回通过"""
        data = {'查询条件': '测试企业', '近一年企业作为被告的涉诉次数': 0}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_lawsuit_count(row)
        assert is_valid is True

    def test_check_lawsuit_count_above_threshold(self):
        """测试涉诉次数超过阈值返回异常"""
        data = {'查询条件': '测试企业', '近一年企业作为被告的涉诉次数': '5'}
        row = pd.Series(data)
        is_valid, msg = self.checker.check_lawsuit_count(row)
        assert is_valid is False
        assert '异常' in msg

    def test_compare_with_previous_no_change(self):
        """测试当前数据与上期一致返回无变更"""
        current_data = {
            '查询条件': '测试企业',
            '法定代表人': '张三',
            '经营范围': '技术开发',
            '股东持股占比': '60%',
            '企业地址': '北京市朝阳区'
        }
        current_row = pd.Series(current_data)
        
        previous_data = {
            '查询条件': ['测试企业'],
            '法定代表人': ['张三'],
            '经营范围': ['技术开发'],
            '股东持股占比': ['60%'],
            '企业地址': ['北京市朝阳区']
        }
        previous_df = pd.DataFrame(previous_data)
        
        results = self.checker.compare_with_previous(current_row, previous_df, '测试企业')
        for is_valid, msg in results:
            assert is_valid is True
            assert '未变更' in msg

    def test_compare_with_previous_changed(self):
        """测试字段值变化返回变更详情"""
        current_data = {
            '查询条件': '测试企业',
            '法定代表人': '李四',
            '经营范围': '技术开发、技术服务',
            '股东持股占比': '60%',
            '企业地址': '北京市朝阳区'
        }
        current_row = pd.Series(current_data)
        
        previous_data = {
            '查询条件': ['测试企业', '其他企业'],
            '法定代表人': ['张三', '王五'],
            '经营范围': ['技术开发', '贸易'],
            '股东持股占比': ['60%', '50%'],
            '企业地址': ['北京市朝阳区', '上海市浦东区']
        }
        previous_df = pd.DataFrame(previous_data)
        
        results = self.checker.compare_with_previous(current_row, previous_df, '测试企业')
        found_change = False
        for is_valid, msg in results:
            if '法定代表人' in msg:
                assert is_valid is False
                assert '已变更' in msg
                assert '张三' in msg
                assert '李四' in msg
                found_change = True
        assert found_change, '未检测到法定代表人变更'

    @patch('check_enterprise.glob.glob')
    @patch('check_enterprise.pd.read_excel')
    @patch('check_enterprise.os.path.exists')
    def test_run_check_mock_excel(self, mock_exists, mock_read_excel, mock_glob):
        """完整流程测试，mock Excel文件输入验证输出格式正确"""
        mock_glob.return_value = ['/tmp/企业信息批量查询列表_20240101_test.xlsx']
        mock_exists.return_value = True
        
        today = datetime.now()
        future_date = (today + timedelta(days=365)).strftime("%Y-%m-%d")
        
        df_data = {
            '查询条件': ['测试企业A', '测试企业B'],
            '登记状态': ['在营（开业）', '在营（开业）'],
            '营业期限': [f'2020-01-01 至 {future_date}', '长期'],
            '注销日期': ['无', '无'],
            '近一年企业作为被告的涉诉次数': ['0', '0'],
            '经营异常名单': ['否', '否'],
            '是否安全生产黑名单': ['否', '否'],
            '是否涉金融黑名单': ['否', '否'],
            '是否存在税务行政处罚': ['否', '否'],
            '是否存在公示处罚信息': ['否', '否'],
            '是否存在工商行政处罚': ['否', '否'],
            '是否严重违法失信企业名单': ['否', '否'],
            '法定代表人': ['张三', '李四'],
            '经营范围': ['技术开发', '技术服务'],
            '股东持股占比': ['60%', '70%'],
            '企业地址': ['北京市朝阳区', '上海市浦东区']
        }
        mock_read_excel.return_value = pd.DataFrame(df_data)
        
        results = self.checker.run_check(today_date='20240101', previous_date=None)
        
        assert len(results) == 2
        assert results[0]['enterprise_name'] == '测试企业A'
        assert results[1]['enterprise_name'] == '测试企业B'
        
        for result in results:
            assert 'checks' in result
            assert 'has_issues' in result
            assert isinstance(result['has_issues'], bool)
            assert len(result['checks']) > 0
