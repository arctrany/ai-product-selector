"""
业务配置测试

测试业务级配置组件，包括过滤器配置、价格计算配置、Excel配置等
"""

import pytest
from common.config.business_config import SelectorFilterConfig, PriceCalculationConfig, ExcelConfig


class TestSelectorFilterConfig:
    """选择器过滤配置测试"""
    
    def test_selector_filter_config_creation_default(self):
        """测试默认过滤配置创建"""
        config = SelectorFilterConfig()
        
        assert config.store_min_sales_30days == 500000.0
        assert config.store_min_orders_30days == 250
        assert config.profit_rate_threshold == 20.0
        assert config.good_store_ratio_threshold == 20.0
        assert config.max_products_to_check == 10
        assert config.item_category_blacklist == []
    
    def test_selector_filter_config_creation_custom(self):
        """测试自定义过滤配置创建"""
        blacklist = ["electronics", "clothing", "books"]
        config = SelectorFilterConfig(
            store_min_sales_30days=1000000.0,
            store_min_orders_30days=500,
            profit_rate_threshold=25.0,
            good_store_ratio_threshold=30.0,
            max_products_to_check=20,
            item_category_blacklist=blacklist
        )
        
        assert config.store_min_sales_30days == 1000000.0
        assert config.store_min_orders_30days == 500
        assert config.profit_rate_threshold == 25.0
        assert config.good_store_ratio_threshold == 30.0
        assert config.max_products_to_check == 20
        assert config.item_category_blacklist == blacklist
    
    def test_store_filtering_thresholds(self):
        """测试店铺过滤阈值配置"""
        # 测试不同销售额阈值
        sales_thresholds = [100000.0, 500000.0, 1000000.0, 5000000.0]
        
        for sales in sales_thresholds:
            config = SelectorFilterConfig(store_min_sales_30days=sales)
            assert config.store_min_sales_30days == sales
        
        # 测试不同订单量阈值
        order_thresholds = [50, 250, 500, 1000]
        
        for orders in order_thresholds:
            config = SelectorFilterConfig(store_min_orders_30days=orders)
            assert config.store_min_orders_30days == orders
    
    def test_profit_rate_thresholds(self):
        """测试利润率阈值配置"""
        profit_rates = [10.0, 15.0, 20.0, 25.0, 30.0]
        
        for rate in profit_rates:
            config = SelectorFilterConfig(profit_rate_threshold=rate)
            assert config.profit_rate_threshold == rate
    
    def test_good_store_ratio_thresholds(self):
        """测试好店比例阈值配置"""
        ratio_thresholds = [10.0, 20.0, 30.0, 50.0]
        
        for ratio in ratio_thresholds:
            config = SelectorFilterConfig(good_store_ratio_threshold=ratio)
            assert config.good_store_ratio_threshold == ratio
    
    def test_products_check_limits(self):
        """测试商品检查数量限制"""
        check_limits = [1, 5, 10, 15, 20, 50]
        
        for limit in check_limits:
            config = SelectorFilterConfig(max_products_to_check=limit)
            assert config.max_products_to_check == limit
    
    def test_category_blacklist_management(self):
        """测试类目黑名单管理"""
        # 测试空黑名单
        config_empty = SelectorFilterConfig()
        assert config_empty.item_category_blacklist == []
        
        # 测试单一类目黑名单
        config_single = SelectorFilterConfig(item_category_blacklist=["electronics"])
        assert config_single.item_category_blacklist == ["electronics"]
        
        # 测试多类目黑名单
        multiple_categories = ["electronics", "clothing", "books", "toys", "sports"]
        config_multiple = SelectorFilterConfig(item_category_blacklist=multiple_categories)
        assert config_multiple.item_category_blacklist == multiple_categories
        assert len(config_multiple.item_category_blacklist) == 5
        
        # 测试中文类目
        chinese_categories = ["电子产品", "服装", "图书", "玩具"]
        config_chinese = SelectorFilterConfig(item_category_blacklist=chinese_categories)
        assert config_chinese.item_category_blacklist == chinese_categories
    
    def test_extreme_values_handling(self):
        """测试极值处理"""
        # 测试极小值
        config_min = SelectorFilterConfig(
            store_min_sales_30days=0.0,
            store_min_orders_30days=0,
            profit_rate_threshold=0.0,
            good_store_ratio_threshold=0.0,
            max_products_to_check=1
        )
        
        assert config_min.store_min_sales_30days == 0.0
        assert config_min.store_min_orders_30days == 0
        assert config_min.max_products_to_check == 1
        
        # 测试极大值
        config_max = SelectorFilterConfig(
            store_min_sales_30days=100000000.0,  # 1亿卢布
            store_min_orders_30days=100000,  # 10万订单
            profit_rate_threshold=100.0,  # 100%利润率
            good_store_ratio_threshold=100.0,  # 100%好店比例
            max_products_to_check=1000  # 检查1000个商品
        )
        
        assert config_max.store_min_sales_30days == 100000000.0
        assert config_max.store_min_orders_30days == 100000
        assert config_max.profit_rate_threshold == 100.0
        assert config_max.good_store_ratio_threshold == 100.0
        assert config_max.max_products_to_check == 1000


class TestPriceCalculationConfig:
    """价格计算配置测试"""
    
    def test_price_calculation_config_creation_default(self):
        """测试默认价格计算配置创建"""
        config = PriceCalculationConfig()
        
        assert config.price_adjustment_threshold_1 == 90.0
        assert config.price_adjustment_threshold_2 == 120.0
        assert config.price_adjustment_amount == 5.0
        assert config.price_multiplier == 2.2
        assert config.pricing_discount_rate == 0.95
        assert config.rub_to_cny_rate == 0.11
        assert config.commission_rate_low_threshold == 1500.0
        assert config.commission_rate_high_threshold == 5000.0
        assert config.commission_rate_default == 12.0
    
    def test_price_calculation_config_creation_custom(self):
        """测试自定义价格计算配置创建"""
        config = PriceCalculationConfig(
            price_adjustment_threshold_1=100.0,
            price_adjustment_threshold_2=150.0,
            price_adjustment_amount=10.0,
            price_multiplier=2.5,
            pricing_discount_rate=0.90,
            rub_to_cny_rate=0.12,
            commission_rate_low_threshold=2000.0,
            commission_rate_high_threshold=6000.0,
            commission_rate_default=15.0
        )
        
        assert config.price_adjustment_threshold_1 == 100.0
        assert config.price_adjustment_threshold_2 == 150.0
        assert config.price_adjustment_amount == 10.0
        assert config.price_multiplier == 2.5
        assert config.pricing_discount_rate == 0.90
        assert config.rub_to_cny_rate == 0.12
        assert config.commission_rate_low_threshold == 2000.0
        assert config.commission_rate_high_threshold == 6000.0
        assert config.commission_rate_default == 15.0
    
    def test_price_adjustment_thresholds(self):
        """测试价格调整阈值"""
        # 测试不同价格阈值组合
        threshold_pairs = [
            (50.0, 80.0),   # 低价区间
            (90.0, 120.0),  # 默认区间
            (100.0, 150.0), # 中价区间
            (200.0, 300.0)  # 高价区间
        ]
        
        for threshold1, threshold2 in threshold_pairs:
            config = PriceCalculationConfig(
                price_adjustment_threshold_1=threshold1,
                price_adjustment_threshold_2=threshold2
            )
            assert config.price_adjustment_threshold_1 == threshold1
            assert config.price_adjustment_threshold_2 == threshold2
            assert config.price_adjustment_threshold_1 < config.price_adjustment_threshold_2
    
    def test_price_multiplier_variations(self):
        """测试价格倍数变化"""
        multipliers = [1.5, 2.0, 2.2, 2.5, 3.0, 4.0]
        
        for multiplier in multipliers:
            config = PriceCalculationConfig(price_multiplier=multiplier)
            assert config.price_multiplier == multiplier
    
    def test_discount_rate_variations(self):
        """测试折扣率变化"""
        discount_rates = [0.80, 0.85, 0.90, 0.95, 0.98, 1.0]
        
        for rate in discount_rates:
            config = PriceCalculationConfig(pricing_discount_rate=rate)
            assert config.pricing_discount_rate == rate
    
    def test_exchange_rate_variations(self):
        """测试汇率变化"""
        exchange_rates = [0.08, 0.10, 0.11, 0.12, 0.15, 0.20]
        
        for rate in exchange_rates:
            config = PriceCalculationConfig(rub_to_cny_rate=rate)
            assert config.rub_to_cny_rate == rate
    
    def test_commission_rate_thresholds(self):
        """测试佣金率阈值"""
        # 测试不同佣金率阈值组合
        commission_configs = [
            (1000.0, 3000.0, 10.0),  # 低阈值
            (1500.0, 5000.0, 12.0),  # 默认阈值
            (2000.0, 8000.0, 15.0),  # 高阈值
            (3000.0, 10000.0, 18.0)  # 很高阈值
        ]
        
        for low, high, default in commission_configs:
            config = PriceCalculationConfig(
                commission_rate_low_threshold=low,
                commission_rate_high_threshold=high,
                commission_rate_default=default
            )
            assert config.commission_rate_low_threshold == low
            assert config.commission_rate_high_threshold == high
            assert config.commission_rate_default == default
            assert config.commission_rate_low_threshold < config.commission_rate_high_threshold
    
    def test_price_calculation_scenarios(self):
        """测试价格计算场景"""
        # 低价商品场景
        config_low = PriceCalculationConfig(
            price_multiplier=1.8,
            pricing_discount_rate=0.98,
            commission_rate_default=8.0
        )
        assert config_low.price_multiplier == 1.8
        assert config_low.pricing_discount_rate == 0.98
        assert config_low.commission_rate_default == 8.0
        
        # 高价商品场景
        config_high = PriceCalculationConfig(
            price_multiplier=3.0,
            pricing_discount_rate=0.85,
            commission_rate_default=20.0
        )
        assert config_high.price_multiplier == 3.0
        assert config_high.pricing_discount_rate == 0.85
        assert config_high.commission_rate_default == 20.0


class TestExcelConfig:
    """Excel配置测试"""
    
    def test_excel_config_creation_default(self):
        """测试默认Excel配置创建"""
        config = ExcelConfig()
        
        assert config.default_excel_path == "uploads/store_list.xlsx"
        assert config.profit_calculator_path == "uploads/profit_calculator.xlsx"
        assert config.store_id_column == "A"
        assert config.good_store_column == "B"
        assert config.status_column == "C"
        assert config.max_rows_to_process == 10000
        assert config.skip_empty_rows is True
    
    def test_excel_config_creation_custom(self):
        """测试自定义Excel配置创建"""
        config = ExcelConfig(
            default_excel_path="data/custom_store_list.xlsx",
            profit_calculator_path="data/custom_calculator.xlsx",
            store_id_column="ID",
            good_store_column="GOOD",
            status_column="STATUS",
            max_rows_to_process=50000,
            skip_empty_rows=False
        )
        
        assert config.default_excel_path == "data/custom_store_list.xlsx"
        assert config.profit_calculator_path == "data/custom_calculator.xlsx"
        assert config.store_id_column == "ID"
        assert config.good_store_column == "GOOD"
        assert config.status_column == "STATUS"
        assert config.max_rows_to_process == 50000
        assert config.skip_empty_rows is False
    
    def test_excel_file_path_variations(self):
        """测试Excel文件路径变化"""
        file_paths = [
            ("uploads/test.xlsx", "uploads/calc.xlsx"),
            ("data/stores.xlsx", "data/profits.xlsx"),
            ("/absolute/path/file.xlsx", "/absolute/path/calc.xlsx"),
            ("./relative/file.xlsx", "./relative/calc.xlsx"),
            ("../parent/file.xlsx", "../parent/calc.xlsx")
        ]
        
        for default_path, calc_path in file_paths:
            config = ExcelConfig(
                default_excel_path=default_path,
                profit_calculator_path=calc_path
            )
            assert config.default_excel_path == default_path
            assert config.profit_calculator_path == calc_path
    
    def test_excel_column_configurations(self):
        """测试Excel列配置"""
        column_configs = [
            ("A", "B", "C"),      # 默认列
            ("ID", "GOOD", "STATUS"),  # 命名列
            ("1", "2", "3"),      # 数字列
            ("店铺ID", "好店", "状态"),  # 中文列名
            ("StoreId", "IsGoodStore", "ProcessStatus")  # 长列名
        ]
        
        for store_col, good_col, status_col in column_configs:
            config = ExcelConfig(
                store_id_column=store_col,
                good_store_column=good_col,
                status_column=status_col
            )
            assert config.store_id_column == store_col
            assert config.good_store_column == good_col
            assert config.status_column == status_col
    
    def test_processing_limits(self):
        """测试处理限制"""
        row_limits = [100, 1000, 10000, 50000, 100000]
        
        for limit in row_limits:
            config = ExcelConfig(max_rows_to_process=limit)
            assert config.max_rows_to_process == limit
    
    def test_empty_row_handling(self):
        """测试空行处理"""
        # 测试跳过空行
        config_skip = ExcelConfig(skip_empty_rows=True)
        assert config_skip.skip_empty_rows is True
        
        # 测试不跳过空行
        config_no_skip = ExcelConfig(skip_empty_rows=False)
        assert config_no_skip.skip_empty_rows is False
    
    def test_excel_config_combinations(self):
        """测试Excel配置组合"""
        # 大数据处理配置
        config_large = ExcelConfig(
            max_rows_to_process=1000000,  # 100万行
            skip_empty_rows=True
        )
        assert config_large.max_rows_to_process == 1000000
        assert config_large.skip_empty_rows is True
        
        # 小数据处理配置
        config_small = ExcelConfig(
            max_rows_to_process=100,  # 100行
            skip_empty_rows=False
        )
        assert config_small.max_rows_to_process == 100
        assert config_small.skip_empty_rows is False
    
    def test_file_extension_variations(self):
        """测试文件扩展名变化"""
        file_extensions = [
            ("file.xlsx", "calc.xlsx"),   # Excel 2007+
            ("file.xls", "calc.xls"),     # Excel 97-2003
            ("file.csv", "calc.csv"),     # CSV格式
            ("file.xlsm", "calc.xlsm")    # Excel宏文件
        ]
        
        for default_file, calc_file in file_extensions:
            config = ExcelConfig(
                default_excel_path=f"data/{default_file}",
                profit_calculator_path=f"data/{calc_file}"
            )
            assert config.default_excel_path.endswith(default_file.split('.')[-1])
            assert config.profit_calculator_path.endswith(calc_file.split('.')[-1])


class TestBusinessConfigIntegration:
    """业务配置集成测试"""
    
    def test_all_business_configs_combination(self):
        """测试所有业务配置组合"""
        filter_config = SelectorFilterConfig(
            store_min_sales_30days=1000000.0,
            profit_rate_threshold=25.0
        )
        
        price_config = PriceCalculationConfig(
            price_multiplier=2.5,
            rub_to_cny_rate=0.12
        )
        
        excel_config = ExcelConfig(
            max_rows_to_process=50000,
            skip_empty_rows=True
        )
        
        # 验证配置独立性
        assert filter_config.store_min_sales_30days == 1000000.0
        assert price_config.price_multiplier == 2.5
        assert excel_config.max_rows_to_process == 50000
    
    def test_conservative_business_config(self):
        """测试保守业务配置"""
        # 保守的过滤配置
        filter_config = SelectorFilterConfig(
            store_min_sales_30days=2000000.0,  # 高销售额要求
            profit_rate_threshold=30.0,  # 高利润率要求
            max_products_to_check=5  # 少量商品检查
        )
        
        # 保守的价格配置
        price_config = PriceCalculationConfig(
            price_multiplier=3.0,  # 高倍数
            pricing_discount_rate=0.90,  # 低折扣
            commission_rate_default=15.0  # 高佣金
        )
        
        # 保守的Excel配置
        excel_config = ExcelConfig(
            max_rows_to_process=1000,  # 少量处理
            skip_empty_rows=True
        )
        
        assert filter_config.store_min_sales_30days == 2000000.0
        assert price_config.price_multiplier == 3.0
        assert excel_config.max_rows_to_process == 1000
    
    def test_aggressive_business_config(self):
        """测试激进业务配置"""
        # 激进的过滤配置
        filter_config = SelectorFilterConfig(
            store_min_sales_30days=100000.0,  # 低销售额要求
            profit_rate_threshold=10.0,  # 低利润率要求
            max_products_to_check=50  # 大量商品检查
        )
        
        # 激进的价格配置
        price_config = PriceCalculationConfig(
            price_multiplier=1.8,  # 低倍数
            pricing_discount_rate=0.98,  # 高折扣
            commission_rate_default=8.0  # 低佣金
        )
        
        # 激进的Excel配置
        excel_config = ExcelConfig(
            max_rows_to_process=100000,  # 大量处理
            skip_empty_rows=False
        )
        
        assert filter_config.store_min_sales_30days == 100000.0
        assert price_config.price_multiplier == 1.8
        assert excel_config.max_rows_to_process == 100000


class TestBusinessConfigValidation:
    """业务配置验证测试"""
    
    def test_filter_config_business_logic(self):
        """测试过滤配置业务逻辑"""
        config = SelectorFilterConfig(
            store_min_sales_30days=500000.0,
            store_min_orders_30days=250,
            profit_rate_threshold=20.0
        )
        
        # 验证业务逻辑合理性
        assert config.store_min_sales_30days > 0
        assert config.store_min_orders_30days > 0
        assert config.profit_rate_threshold > 0
        assert config.profit_rate_threshold <= 100  # 利润率不应超过100%
    
    def test_price_config_business_logic(self):
        """测试价格配置业务逻辑"""
        config = PriceCalculationConfig()
        
        # 验证价格阈值逻辑
        assert config.price_adjustment_threshold_1 < config.price_adjustment_threshold_2
        
        # 验证佣金阈值逻辑
        assert config.commission_rate_low_threshold < config.commission_rate_high_threshold
        
        # 验证汇率合理性
        assert 0 < config.rub_to_cny_rate < 1  # 卢布对人民币汇率应在0-1之间
        
        # 验证折扣率合理性
        assert 0 < config.pricing_discount_rate <= 1  # 折扣率应在0-1之间
    
    def test_excel_config_business_logic(self):
        """测试Excel配置业务逻辑"""
        config = ExcelConfig()
        
        # 验证文件路径格式
        assert config.default_excel_path.endswith('.xlsx')
        assert config.profit_calculator_path.endswith('.xlsx')
        
        # 验证处理限制合理性
        assert config.max_rows_to_process > 0
        assert config.max_rows_to_process <= 10000000  # 不超过1000万行
