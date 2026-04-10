#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业信息检查器单元测试
使用pytest框架和unittest.mock进行测试
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_enterprise import EnterpriseChecker, EnterpriseCheckerError


class TestCheckBusinessStatus:
    """测试营业状态检查功能"""

    def test_check_business_status_normal(self):
        """
        测试营业状态正常返回通过
        当登记状态为'在营（开业）'时，应返回True和正常消息
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'登记状态': '在营（开业）'})
        
        is_valid, msg = checker.check_business_status(row)
        
        assert is_valid is True
        assert '在营（开业）' in msg
        assert '[异常]' not in msg

    def test_check_business_status_revoked(self):
        """
        测试吊销状态返回异常
        当登记状态为'吊销'时，应返回False和异常标记
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'登记状态': '吊销'})
        
        is_valid, msg = checker.check_business_status(row)
        
        assert is_valid is False
        assert '吊销' in msg
        assert '[异常]' in msg

    def test_check_business_status_cancelled(self):
        """
        测试注销状态返回异常
        当登记状态为'注销'时，应返回False和异常标记
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'登记状态': '注销'})
        
        is_valid, msg = checker.check_business_status(row)
        
        assert is_valid is False
        assert '注销' in msg
        assert '[异常]' in msg

    def test_check_business_status_with_whitespace(self):
        """
        测试带空格的营业状态处理
        状态值前后有空格时应正确去除空格后判断
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'登记状态': '  在营（开业）  '})
        
        is_valid, msg = checker.check_business_status(row)
        
        assert is_valid is True


class TestCheckBusinessPeriod:
    """测试营业期限检查功能"""

    def test_check_business_period_valid(self):
        """
        测试营业期限在有效期内返回通过
        当营业期限结束日期晚于今天时，应返回True
        """
        checker = EnterpriseChecker(base_path='./test_data')
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        row = pd.Series({'营业期限': f'2018-03-16 至 {future_date}'})
        
        is_valid, msg = checker.check_business_period(row)
        
        assert is_valid is True
        assert '[有效]' in msg

    def test_check_business_period_expired(self):
        """
        测试营业期限已过期返回异常
        当营业期限结束日期早于今天时，应返回False
        """
        checker = EnterpriseChecker(base_path='./test_data')
        past_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        row = pd.Series({'营业期限': f'2018-03-16 至 {past_date}'})
        
        is_valid, msg = checker.check_business_period(row)
        
        assert is_valid is False
        assert '[已过期]' in msg

    def test_check_business_period_long_term(self):
        """
        测试"长期"营业期限返回通过
        当营业期限包含"长期"字样时，应视为长期有效
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'营业期限': '长期'})
        
        is_valid, msg = checker.check_business_period(row)
        
        assert is_valid is True
        assert '[长期有效]' in msg

    def test_check_business_period_no_fixed_term(self):
        """
        测试"无固定期限"营业期限返回通过
        当营业期限包含"无固定期限"字样时，应视为长期有效
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'营业期限': '无固定期限'})
        
        is_valid, msg = checker.check_business_period(row)
        
        assert is_valid is True
        assert '[长期有效]' in msg

    def test_check_business_period_contains_long_term(self):
        """
        测试包含"长期"字样的营业期限
        只要包含"长期"两字即视为长期有效
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'营业期限': '2018-03-16 至 长期'})
        
        is_valid, msg = checker.check_business_period(row)
        
        assert is_valid is True
        assert '[长期有效]' in msg


class TestCheckLawsuitCount:
    """测试涉诉次数检查功能"""

    def test_check_lawsuit_count_zero(self):
        """
        测试涉诉次数为0返回通过
        当近一年企业作为被告的涉诉次数为0时，应返回True
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'近一年企业作为被告的涉诉次数': 0})
        
        is_valid, msg = checker.check_lawsuit_count(row)
        
        assert is_valid is True
        assert '0' in msg
        assert '[异常]' not in msg

    def test_check_lawsuit_count_zero_float(self):
        """
        测试涉诉次数为0.0（浮点数）返回通过
        支持浮点数0.0的判断
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'近一年企业作为被告的涉诉次数': 0.0})
        
        is_valid, msg = checker.check_lawsuit_count(row)
        
        assert bool(is_valid) is True

    def test_check_lawsuit_count_zero_string(self):
        """
        测试涉诉次数为字符串'0'返回通过
        支持字符串格式的0
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'近一年企业作为被告的涉诉次数': '0'})
        
        is_valid, msg = checker.check_lawsuit_count(row)
        
        assert is_valid is True

    def test_check_lawsuit_count_zero_with_suffix(self):
        """
        测试涉诉次数为'0次'返回通过
        支持带"次"单位的格式
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'近一年企业作为被告的涉诉次数': '0次'})
        
        is_valid, msg = checker.check_lawsuit_count(row)
        
        assert is_valid is True

    def test_check_lawsuit_count_exceeds_threshold(self):
        """
        测试涉诉次数超过阈值返回异常
        当涉诉次数大于0时，应返回False和异常标记
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'近一年企业作为被告的涉诉次数': 5})
        
        is_valid, msg = checker.check_lawsuit_count(row)
        
        assert is_valid is False
        assert '5' in msg
        assert '[异常]' in msg

    def test_check_lawsuit_count_string_number(self):
        """
        测试涉诉次数为字符串数字返回异常
        字符串格式的非零数字应返回异常
        """
        checker = EnterpriseChecker(base_path='./test_data')
        row = pd.Series({'近一年企业作为被告的涉诉次数': '3'})
        
        is_valid, msg = checker.check_lawsuit_count(row)
        
        assert is_valid is False
        assert '[异常]' in msg


class TestCompareWithPrevious:
    """测试与上期数据比较功能"""

    def test_compare_with_previous_no_change(self):
        """
        测试当前数据与上期一致返回无变更
        当所有比较字段值都相同时，应返回全部通过的结果
        """
        checker = EnterpriseChecker(base_path='./test_data')
        
        current_row = pd.Series({
            '查询条件': '测试企业',
            '法定代表人': '张三',
            '经营范围': '软件开发',
            '股东持股占比': '100%',
            '企业地址': '北京市'
        })
        
        previous_df = pd.DataFrame({
            '查询条件': ['测试企业'],
            '法定代表人': ['张三'],
            '经营范围': ['软件开发'],
            '股东持股占比': ['100%'],
            '企业地址': ['北京市']
        })
        
        results = checker.compare_with_previous(current_row, previous_df, '测试企业')
        
        assert len(results) == 4
        for is_valid, msg in results:
            assert is_valid is True
            assert '未变更' in msg

    def test_compare_with_previous_has_changes(self):
        """
        测试字段值变化返回变更详情
        当字段值发生变化时，应返回False和详细的变更信息
        """
        checker = EnterpriseChecker(base_path='./test_data')
        
        current_row = pd.Series({
            '查询条件': '测试企业',
            '法定代表人': '李四',  # 变更了
            '经营范围': '软件开发',
            '股东持股占比': '100%',
            '企业地址': '上海市'  # 变更了
        })
        
        previous_df = pd.DataFrame({
            '查询条件': ['测试企业'],
            '法定代表人': ['张三'],
            '经营范围': ['软件开发'],
            '股东持股占比': ['100%'],
            '企业地址': ['北京市']
        })
        
        results = checker.compare_with_previous(current_row, previous_df, '测试企业')
        
        assert len(results) == 4
        
        # 检查法定代表人变更
        legal_rep_result = [r for r in results if '法定代表人' in r[1]][0]
        assert legal_rep_result[0] is False
        assert '已变更' in legal_rep_result[1]
        assert '原值: 张三' in legal_rep_result[1]
        assert '现值: 李四' in legal_rep_result[1]
        
        # 检查企业地址变更
        address_result = [r for r in results if '企业地址' in r[1]][0]
        assert address_result[0] is False
        assert '已变更' in address_result[1]

    def test_compare_with_previous_enterprise_not_found(self):
        """
        测试上期数据中找不到企业
        当上期数据中没有该企业时，应返回提示信息
        """
        checker = EnterpriseChecker(base_path='./test_data')
        
        current_row = pd.Series({
            '查询条件': '测试企业',
            '法定代表人': '张三',
            '经营范围': '软件开发',
            '股东持股占比': '100%',
            '企业地址': '北京市'
        })
        
        previous_df = pd.DataFrame({
            '查询条件': ['其他企业'],
            '法定代表人': ['李四'],
            '经营范围': ['餐饮服务'],
            '股东持股占比': ['50%'],
            '企业地址': ['上海市']
        })
        
        results = checker.compare_with_previous(current_row, previous_df, '测试企业')
        
        assert len(results) == 1
        assert results[0][0] is True
        assert '前一天无此企业记录' in results[0][1]


class TestRunCheck:
    """测试完整流程"""

    @patch('os.path.exists')
    @patch('check_enterprise.pd.read_excel')
    @patch('check_enterprise.glob.glob')
    @patch.object(EnterpriseChecker, '_print_model_info')
    def test_run_check_success(self, mock_print_info, mock_glob, mock_read_excel, mock_exists):
        """
        测试完整流程，mock Excel文件输入验证输出格式正确
        验证run_check方法能正确加载数据并返回格式正确的检查结果
        """
        # Mock文件查找和文件存在检查
        mock_glob.return_value = ['/fake/path/企业信息批量查询列表_20240101.xlsx']
        mock_exists.return_value = True
        
        # 构造测试用的DataFrame
        test_df = pd.DataFrame({
            '查询条件': ['测试企业1', '测试企业2'],
            '登记状态': ['在营（开业）', '在营（开业）'],
            '营业期限': ['2018-03-16 至 2038-03-15', '长期'],
            '注销日期': ['无', '无'],
            '近一年企业作为被告的涉诉次数': [0, 0],
            '经营异常名单': ['否', '否'],
            '是否安全生产黑名单': ['否', '否'],
            '是否涉金融黑名单': ['否', '否'],
            '是否存在税务行政处罚': ['否', '否'],
            '是否存在公示处罚信息': ['否', '否'],
            '是否存在工商行政处罚': ['否', '否'],
            '是否严重违法失信企业名单': ['否', '否'],
            '法定代表人': ['张三', '李四'],
            '经营范围': ['软件开发', '餐饮服务'],
            '股东持股占比': ['100%', '50%'],
            '企业地址': ['北京市', '上海市']
        })
        
        mock_read_excel.return_value = test_df
        
        checker = EnterpriseChecker(base_path='./test_data')
        results = checker.run_check(today_date='20240101')
        
        # 验证结果格式
        assert isinstance(results, list)
        assert len(results) == 2
        
        for result in results:
            # 验证每个结果包含必需的字段
            assert 'enterprise_name' in result
            assert 'checks' in result
            assert 'has_issues' in result
            assert isinstance(result['checks'], list)
            assert isinstance(result['has_issues'], bool)
            
            # 验证checks中的每个检查项格式
            for check in result['checks']:
                assert isinstance(check, tuple)
                assert len(check) == 2
                assert isinstance(check[0], bool)
                assert isinstance(check[1], str)

    @patch('os.path.exists')
    @patch('check_enterprise.pd.read_excel')
    @patch('check_enterprise.glob.glob')
    @patch.object(EnterpriseChecker, '_print_model_info')
    def test_run_check_with_previous_comparison(self, mock_print_info, mock_glob, mock_read_excel, mock_exists):
        """
        测试包含上期数据比较的完整流程
        验证当提供previous_date时能正确进行比较检查
        """
        # Mock文件查找 - 今天和昨天的文件
        def mock_glob_side_effect(pattern):
            if '20240101' in pattern:
                return ['/fake/path/企业信息批量查询列表_20240101.xlsx']
            elif '20231231' in pattern:
                return ['/fake/path/企业信息批量查询列表_20231231.xlsx']
            return []
        
        mock_glob.side_effect = mock_glob_side_effect
        mock_exists.return_value = True
        
        # 今天的数据
        today_df = pd.DataFrame({
            '查询条件': ['测试企业1'],
            '登记状态': ['在营（开业）'],
            '营业期限': ['2018-03-16 至 2038-03-15'],
            '注销日期': ['无'],
            '近一年企业作为被告的涉诉次数': [0],
            '经营异常名单': ['否'],
            '是否安全生产黑名单': ['否'],
            '是否涉金融黑名单': ['否'],
            '是否存在税务行政处罚': ['否'],
            '是否存在公示处罚信息': ['否'],
            '是否存在工商行政处罚': ['否'],
            '是否严重违法失信企业名单': ['否'],
            '法定代表人': ['李四'],  # 变更了
            '经营范围': ['软件开发'],
            '股东持股占比': ['100%'],
            '企业地址': ['北京市']
        })
        
        # 昨天的数据
        yesterday_df = pd.DataFrame({
            '查询条件': ['测试企业1'],
            '登记状态': ['在营（开业）'],
            '营业期限': ['2018-03-16 至 2038-03-15'],
            '注销日期': ['无'],
            '近一年企业作为被告的涉诉次数': [0],
            '经营异常名单': ['否'],
            '是否安全生产黑名单': ['否'],
            '是否涉金融黑名单': ['否'],
            '是否存在税务行政处罚': ['否'],
            '是否存在公示处罚信息': ['否'],
            '是否存在工商行政处罚': ['否'],
            '是否严重违法失信企业名单': ['否'],
            '法定代表人': ['张三'],
            '经营范围': ['软件开发'],
            '股东持股占比': ['100%'],
            '企业地址': ['北京市']
        })
        
        def mock_read_excel_side_effect(path):
            if '20240101' in path:
                return today_df
            elif '20231231' in path:
                return yesterday_df
            raise ValueError(f"Unknown path: {path}")
        
        mock_read_excel.side_effect = mock_read_excel_side_effect
        
        checker = EnterpriseChecker(base_path='./test_data')
        results = checker.run_check(today_date='20240101', previous_date='20231231')
        
        # 验证结果包含比较检查
        assert len(results) == 1
        result = results[0]
        
        # 查找法定代表人变更的检查项
        legal_rep_checks = [c for c in result['checks'] if '法定代表人' in c[1]]
        assert len(legal_rep_checks) > 0
        
        # 应该有变更标记
        change_check = [c for c in legal_rep_checks if '已变更' in c[1]]
        assert len(change_check) > 0
        assert change_check[0][0] is False  # 变更了所以返回False

    @patch('check_enterprise.glob.glob')
    @patch.object(EnterpriseChecker, '_print_model_info')
    def test_run_check_file_not_found(self, mock_print_info, mock_glob):
        """
        测试文件未找到时抛出异常
        当找不到对应日期的文件时，应抛出EnterpriseCheckerError
        """
        mock_glob.return_value = []
        
        checker = EnterpriseChecker(base_path='./test_data')
        
        with pytest.raises(EnterpriseCheckerError) as exc_info:
            checker.run_check(today_date='20240101')
        
        assert '未找到日期为' in str(exc_info.value)


class TestEnterpriseCheckerEdgeCases:
    """测试边界情况"""

    def test_validate_columns_missing(self):
        """
        测试缺少必需列时抛出异常
        当Excel文件缺少必需列时，应抛出EnterpriseCheckerError
        """
        checker = EnterpriseChecker(base_path='./test_data')
        
        # 缺少必需列的DataFrame
        df = pd.DataFrame({
            '查询条件': ['测试企业'],
            # 缺少其他必需列
        })
        
        with pytest.raises(EnterpriseCheckerError) as exc_info:
            checker._validate_columns(df, '/fake/path.xlsx')
        
        assert '缺少必需的列' in str(exc_info.value)

    @patch('os.path.exists')
    def test_load_excel_file_not_exists(self, mock_exists):
        """
        测试加载不存在的文件
        当文件不存在时，应抛出EnterpriseCheckerError
        """
        mock_exists.return_value = False
        checker = EnterpriseChecker(base_path='./test_data')
        
        with pytest.raises(EnterpriseCheckerError) as exc_info:
            checker.load_excel('/fake/nonexistent.xlsx')
        
        assert '文件不存在' in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
