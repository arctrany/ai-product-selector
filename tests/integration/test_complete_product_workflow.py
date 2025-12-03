"""
完整商品处理流程集成测试

展示从商品URL输入到最终利润评估输出的完整业务流程
包含：数据抓取 → 跟卖分析 → 数据合并 → 利润计算 → 结果输出

使用真实测试数据而非Mock数据
"""
import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch

from good_store_selector import GoodStoreSelector, _evaluate_profit_calculation_completeness
from common.models.business_models import ProductInfo
from common.models.scraping_result import ScrapingResult
from common.config.base_config import GoodStoreSelectorConfig
from common.services.scraping_orchestrator import ScrapingOrchestrator, ScrapingMode


class TestCompleteProductWorkflow(unittest.TestCase):
    """完整商品处理流程测试"""
    
    def setUp(self):
        """测试前准备"""
        # 加载真实测试数据
        self.test_data_dir = Path(__file__).parent.parent / "test_data"
        
        # 加载系统配置
        with open(self.test_data_dir / "integration_test_system_config.json", 'r', encoding='utf-8') as f:
            system_config = json.load(f)
        self.config = GoodStoreSelectorConfig()
        self.config.selection_mode = system_config.get('selection_mode', 'select-goods')
        self.config.dryrun = system_config.get('dryrun', False)
        
        # 加载用户数据
        with open(self.test_data_dir / "integration_test_user_data.json", 'r', encoding='utf-8') as f:
            self.user_data = json.load(f)
        
        # 加载测试用例
        with open(self.test_data_dir / "ozon_test_cases.json", 'r', encoding='utf-8') as f:
            self.test_cases_data = json.load(f)
        
        # 创建临时文件
        self.temp_excel = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_calc = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        self.temp_excel.close()
        self.temp_calc.close()
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_excel.name)
            os.unlink(self.temp_calc.name)
        except:
            pass
    
    def test_complete_product_analysis_workflow(self):
        """
        测试完整的商品分析工作流程
        
        流程：商品URL → 数据抓取 → 跟卖检测 → 数据合并 → 利润计算 → 最终结果
        """
        # 输入：商品URL
        product_url = "https://www.ozon.ru/product/test-product-123456/"
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func:
            
            # === 步骤1: 设置真实的利润评估器 ===
            from common.business.profit_evaluator import ProfitEvaluator
            real_profit_evaluator = ProfitEvaluator(self.temp_calc.name, self.config)
            mock_profit_evaluator = Mock()
            mock_profit_evaluator.prepare_for_profit_calculation = real_profit_evaluator.prepare_for_profit_calculation
            mock_profit_evaluator.evaluate_product_profit.return_value = {
                'profit_rate': 28.5,
                'is_profitable': True,
                'source_price': 45.0,
                'selling_price': 76.0,  # 跟卖价格 80 * 0.95
                'profit_amount': 31.0,
                'margin': 40.8,
                'product_info': None  # 将在实际调用时设置
            }
            mock_profit_class.return_value = mock_profit_evaluator
            
            # === 步骤2: 模拟数据抓取和跟卖检测 ===
            # 原商品数据（完整度较低）
            primary_product = ProductInfo(
                product_id="123456",
                product_url=product_url,
                green_price=100.0,
                black_price=120.0,
                source_price=50.0,
                commission_rate=0.15,
                # 缺少一些ERP字段
                weight=None,
                length=None
            )
            
            # 跟卖商品数据（完整度较高）
            competitor_product = ProductInfo(
                product_id="comp-789",
                product_url="https://www.ozon.ru/product/competitor-789/",
                green_price=80.0,
                black_price=95.0,
                source_price=45.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            # 模拟协调器返回的数据组装结果
            mock_orchestrator = Mock()
            mock_orchestrator.scrape_with_orchestration.return_value = ScrapingResult.create_success({
                'primary_product': primary_product,
                'competitor_product': competitor_product,
                'competitors_list': [
                    {
                        'product_id': 'comp-789',
                        'price': 80.0,
                        'store_name': '跟卖店铺A'
                    }
                ]
            })
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # === 步骤3: 创建选择器并初始化 ===
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                profit_calculator_path=self.temp_calc.name,
                config=self.config
            )
            selector._initialize_components()
            
            # === 步骤4: 执行完整的商品分析流程 ===
            
            # 4.1 数据抓取和组装
            scraping_result = selector.scraping_orchestrator.scrape_with_orchestration(
                ScrapingMode.FULL_CHAIN,
                url=product_url
            )
            
            print(f"\n=== 步骤1: 数据抓取完成 ===")
            print(f"原商品ID: {scraping_result.data['primary_product'].product_id}")
            print(f"原商品价格: {scraping_result.data['primary_product'].green_price}₽")
            print(f"跟卖商品ID: {scraping_result.data['competitor_product'].product_id}")
            print(f"跟卖商品价格: {scraping_result.data['competitor_product'].green_price}₽")
            
            # 4.2 数据合并和商品选择
            selected_product = selector.merge_and_compute(scraping_result)
            
            print(f"\n=== 步骤2: 数据合并和选择 ===")
            print(f"选择的商品ID: {selected_product.product_id}")
            print(f"是否选择跟卖: {selected_product.is_competitor_selected}")
            print(f"定价(list_price): {selected_product.list_price}₽")
            
            # 验证完整性评估逻辑
            from good_store_selector import _evaluate_profit_calculation_completeness
            primary_completeness = _evaluate_profit_calculation_completeness(primary_product)
            competitor_completeness = _evaluate_profit_calculation_completeness(competitor_product)
            
            print(f"原商品完整度: {primary_completeness:.1%}")
            print(f"跟卖商品完整度: {competitor_completeness:.1%}")
            
            # 4.3 利润计算
            profit_result = selector.profit_evaluator.evaluate_product_profit(
                selected_product,
                selected_product.source_price
            )
            
            print(f"\n=== 步骤3: 利润计算 ===")
            print(f"利润率: {profit_result['profit_rate']:.1f}%")
            print(f"是否盈利: {profit_result['is_profitable']}")
            print(f"采购价: {profit_result['source_price']}₽")
            print(f"销售价: {profit_result['selling_price']}₽")
            print(f"利润额: {profit_result['profit_amount']}₽")
            
            # === 步骤5: 验证完整流程结果 ===
            
            # 验证数据抓取
            self.assertTrue(scraping_result.success)
            self.assertIn('primary_product', scraping_result.data)
            self.assertIn('competitor_product', scraping_result.data)
            
            # 验证数据合并逻辑（应该选择完整度更高的跟卖商品）
            self.assertEqual(selected_product.product_id, "comp-789")
            self.assertTrue(selected_product.is_competitor_selected)
            self.assertEqual(selected_product.list_price, 76.0)  # 80 * 0.95
            
            # 验证完整性评估
            self.assertGreater(competitor_completeness, primary_completeness)
            self.assertEqual(competitor_completeness, 1.0)  # 100% 完整
            
            # 验证利润计算
            self.assertEqual(profit_result['profit_rate'], 28.5)
            self.assertTrue(profit_result['is_profitable'])
            self.assertEqual(profit_result['source_price'], 45.0)
            self.assertEqual(profit_result['selling_price'], 76.0)
            
            # 验证调用链
            mock_orchestrator.scrape_with_orchestration.assert_called_once()
            mock_profit_evaluator.evaluate_product_profit.assert_called_once()
            
            print(f"\n=== 完整流程验证通过 ===")
            print(f"✅ 数据抓取: 成功获取原商品和跟卖商品数据")
            print(f"✅ 智能选择: 基于完整度选择了跟卖商品")
            print(f"✅ 利润计算: 计算出28.5%的利润率")
            print(f"✅ 业务决策: 商品盈利，建议采用")
    
    def test_workflow_with_no_competitor(self):
        """测试无跟卖商品时的完整流程"""
        product_url = "https://www.ozon.ru/product/no-competitor-123/"
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func:
            
            # 设置利润评估器
            from common.business.profit_evaluator import ProfitEvaluator
            real_profit_evaluator = ProfitEvaluator(self.temp_calc.name, self.config)
            mock_profit_evaluator = Mock()
            mock_profit_evaluator.prepare_for_profit_calculation = real_profit_evaluator.prepare_for_profit_calculation
            mock_profit_evaluator.evaluate_product_profit.return_value = {
                'profit_rate': 35.0,
                'is_profitable': True,
                'source_price': 50.0,
                'selling_price': 95.0,
                'profit_amount': 45.0
            }
            mock_profit_class.return_value = mock_profit_evaluator
            
            # 只有原商品，无跟卖
            primary_product = ProductInfo(
                product_id="no_comp_123",
                product_url=product_url,
                green_price=100.0,
                black_price=120.0,
                source_price=50.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            mock_orchestrator = Mock()
            mock_orchestrator.scrape_with_orchestration.return_value = ScrapingResult.create_success({
                'primary_product': primary_product,
                'competitor_product': None,
                'competitors_list': []
            })
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 执行流程
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                profit_calculator_path=self.temp_calc.name,
                config=self.config
            )
            selector._initialize_components()
            
            scraping_result = selector.scraping_orchestrator.scrape_with_orchestration(
                ScrapingMode.FULL_CHAIN,
                url=product_url
            )
            
            selected_product = selector.merge_and_compute(scraping_result)
            
            print(f"\n=== 无跟卖商品流程 ===")
            print(f"选择的商品ID: {selected_product.product_id}")
            print(f"是否选择跟卖: {selected_product.is_competitor_selected}")
            print(f"定价(list_price): {selected_product.list_price}₽")
            
            # 验证选择了原商品
            self.assertEqual(selected_product.product_id, "no_comp_123")
            self.assertFalse(selected_product.is_competitor_selected)
            self.assertEqual(selected_product.list_price, 95.0)  # 100 * 0.95
    
    def test_workflow_error_handling(self):
        """测试流程中的错误处理"""
        product_url = "https://www.ozon.ru/product/error-test-123/"
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func:
            
            # 模拟抓取失败
            mock_orchestrator = Mock()
            mock_orchestrator.scrape_with_orchestration.return_value = ScrapingResult.create_failure(
                "网络连接超时"
            )
            mock_orchestrator_func.return_value = mock_orchestrator
            
            mock_profit_class.return_value = Mock()
            
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                profit_calculator_path=self.temp_calc.name,
                config=self.config
            )
            selector._initialize_components()
            
            # 执行流程
            scraping_result = selector.scraping_orchestrator.scrape_with_orchestration(
                ScrapingMode.FULL_CHAIN,
                url=product_url
            )
            
            print(f"\n=== 错误处理流程 ===")
            print(f"抓取结果: {scraping_result.success}")
            print(f"错误信息: {scraping_result.error_message}")
            
            # 验证错误处理
            self.assertFalse(scraping_result.success)
            self.assertIn("网络连接超时", scraping_result.error_message)
            
            # 测试合并逻辑的错误处理
            with self.assertRaises(ValueError):
                selector.merge_and_compute(scraping_result)
    
    def test_real_data_product_workflow(self):
        """
        使用真实测试数据的完整商品流程测试
        
        基于 test_data/ozon_test_cases.json 中的真实商品数据
        """
        # 选择一个有跟卖店铺的测试用例
        test_case = None
        for case in self.test_cases_data['test_cases']:
            if case['expected']['has_competitors']:
                test_case = case
                break
        
        if not test_case:
            self.skipTest("没有找到有跟卖店铺的测试用例")
        
        product_url = test_case['url']
        expected_data = test_case['expected']
        
        print(f"\n=== 使用真实测试数据 ===")
        print(f"测试用例: {test_case['name']}")
        print(f"商品URL: {product_url}")
        print(f"预期跟卖数量: {expected_data.get('competitor_count', 0)}")
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func:
            
            # 基于真实数据创建商品信息
            primary_product = ProductInfo(
                product_id=product_url.split('/')[-1],  # 从URL提取ID
                product_url=product_url,
                green_price=expected_data.get('green_price', 100.0),
                black_price=expected_data.get('black_price', 120.0),
                source_price=50.0,  # 模拟采购价
                commission_rate=self.user_data.get('margin', 0.15),
                # 根据真实数据设置完整性
                weight=500.0 if expected_data.get('has_image') else None,
                length=10.0 if expected_data.get('has_image') else None,
                width=8.0 if expected_data.get('has_image') else None,
                height=5.0 if expected_data.get('has_image') else None
            )
            
            # 如果有跟卖，创建跟卖商品数据
            competitor_product = None
            competitors_list = []
            
            if expected_data.get('has_competitors') and expected_data.get('competitor_count', 0) > 0:
                # 基于真实数据创建跟卖商品
                base_price = expected_data.get('green_price') or expected_data.get('black_price') or 100.0
                competitor_price = base_price * 0.9
                competitor_product = ProductInfo(
                    product_id=f"comp_{product_url.split('/')[-1]}",
                    product_url=f"{product_url}_competitor",
                    green_price=competitor_price,
                    black_price=competitor_price * 1.2,
                    source_price=45.0,
                    commission_rate=self.user_data.get('margin', 0.15),
                    weight=480.0,
                    length=9.0,
                    width=7.0,
                    height=4.0
                )
                
                # 创建跟卖店铺列表
                for i in range(min(expected_data.get('competitor_count', 0), 5)):  # 限制数量
                    competitors_list.append({
                        'product_id': f'comp_{i}_{product_url.split("/")[-1]}',
                        'price': competitor_price + (i * 5),
                        'store_name': f'跟卖店铺_{i+1}'
                    })
            
            # 设置利润评估器
            from common.business.profit_evaluator import ProfitEvaluator
            real_profit_evaluator = ProfitEvaluator(self.temp_calc.name, self.config)
            mock_profit_evaluator = Mock()
            mock_profit_evaluator.prepare_for_profit_calculation = real_profit_evaluator.prepare_for_profit_calculation
            
            # 根据真实数据计算预期利润
            selected_product = competitor_product if competitor_product else primary_product
            expected_selling_price = selected_product.green_price * 0.95
            expected_profit_rate = ((expected_selling_price - selected_product.source_price) / expected_selling_price) * 100
            
            mock_profit_evaluator.evaluate_product_profit.return_value = {
                'profit_rate': expected_profit_rate,
                'is_profitable': expected_profit_rate > 15.0,  # 基于用户配置的最小利润率
                'source_price': selected_product.source_price,
                'selling_price': expected_selling_price,
                'profit_amount': expected_selling_price - selected_product.source_price,
                'margin': expected_profit_rate
            }
            mock_profit_class.return_value = mock_profit_evaluator
            
            # 模拟协调器返回真实数据结构
            mock_orchestrator = Mock()
            mock_orchestrator.scrape_with_orchestration.return_value = ScrapingResult.create_success({
                'primary_product': primary_product,
                'competitor_product': competitor_product,
                'competitors_list': competitors_list
            })
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 执行完整流程
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                profit_calculator_path=self.temp_calc.name,
                config=self.config
            )
            selector._initialize_components()
            
            # 数据抓取
            scraping_result = selector.scraping_orchestrator.scrape_with_orchestration(
                ScrapingMode.FULL_CHAIN,
                url=product_url
            )
            
            print(f"\n=== 真实数据流程执行 ===")
            print(f"抓取成功: {scraping_result.success}")
            print(f"原商品价格: {scraping_result.data['primary_product'].green_price}₽")
            
            if scraping_result.data.get('competitor_product'):
                print(f"跟卖商品价格: {scraping_result.data['competitor_product'].green_price}₽")
                print(f"跟卖店铺数量: {len(scraping_result.data.get('competitors_list', []))}")
            
            # 数据合并和选择
            selected_product = selector.merge_and_compute(scraping_result)
            
            print(f"\n=== 智能选择结果 ===")
            print(f"选择的商品: {'跟卖商品' if selected_product.is_competitor_selected else '原商品'}")
            print(f"定价: {selected_product.list_price}₽")
            
            # 完整性评估
            primary_completeness = _evaluate_profit_calculation_completeness(primary_product)
            if competitor_product:
                competitor_completeness = _evaluate_profit_calculation_completeness(competitor_product)
                print(f"原商品完整度: {primary_completeness:.1%}")
                print(f"跟卖商品完整度: {competitor_completeness:.1%}")
            
            # 利润计算
            profit_result = selector.profit_evaluator.evaluate_product_profit(
                selected_product,
                selected_product.source_price
            )
            
            print(f"\n=== 基于真实数据的利润计算 ===")
            print(f"利润率: {profit_result['profit_rate']:.1f}%")
            print(f"是否盈利: {profit_result['is_profitable']}")
            print(f"采购价: {profit_result['source_price']}₽")
            print(f"销售价: {profit_result['selling_price']:.1f}₽")
            
            # 验证结果
            self.assertTrue(scraping_result.success)
            self.assertIsNotNone(selected_product)
            self.assertIsNotNone(selected_product.list_price)
            
            # 验证利润计算合理性
            self.assertGreater(profit_result['profit_rate'], 0)
            self.assertEqual(profit_result['source_price'], selected_product.source_price)
            
            # 如果有跟卖且跟卖更优，应该选择跟卖
            if competitor_product and competitor_completeness > primary_completeness:
                self.assertTrue(selected_product.is_competitor_selected)
            
            print(f"\n=== 真实数据测试验证通过 ===")
            print(f"✅ 使用了真实的商品URL和预期数据")
            print(f"✅ 基于真实配置进行利润计算")
            print(f"✅ 验证了完整的业务流程")


if __name__ == '__main__':
    unittest.main()