"""
Pre-compiled Excel calculation rules

This file contains the pre-compiled Excel logic extracted from profits_calculator.xlsx.
It implements the complete profit calculation logic including the 6 shipping channels
with their full conditional logic.

Source: docs/profits_calculator.xlsx
Sheets: UNI运费, 利润计算表
Last compiled: 2025-12-05
"""

from typing import Dict, Any, Optional, Tuple, List
import math


class CompiledExcelRules:
    """Pre-compiled Excel calculation rules"""

    def __init__(self):
        """Initialize with Excel constants and lookup tables"""
        # Constants from Excel (利润计算表)
        self.constants = {
            "fixed_label_fee": 3.0,  # D11: 贴单费 (fixed at 3)
            "misc_fee_rate": 0.04,   # F11: 杂费 = A11 * 0.04
            "commission_rate_factor": 0.01,  # 佣金率转换因子
        }

        # =================================================================
        # Shipping Channels from UNI运费 Sheet (K8, K15, K22, K29, K36, K43)
        # Each channel has conditions and pricing formula:
        # =IF(AND(MAX($M$4:$M$6)<=V, SUM($M$4:$M$6)<=U, $M$7<=W, $M$7>=X, $M$3>=S, $M$3<=T),
        #     IF($M$8="自提点", Y + $M$3*Z, AA + $M$3*AB), "")
        #
        # M3: weight(g), M4-M6: dimensions(cm), M7: price(RUB), M8: delivery_type
        # =================================================================
        self.shipping_channels = [
            {
                'name': 'UNI Extra Small',  # K8
                'weight_min': 1,
                'weight_max': 500,
                'sum_dim_max': 90,
                'max_dim': 60,
                'price_max': 1500,
                'price_min': 0,
                'pickup_base': 3,
                'pickup_per_g': 0.025,
                'delivery_base': None,  # Not available
                'delivery_per_g': None,
            },
            {
                'name': 'UNI Budget',  # K15
                'weight_min': 501,
                'weight_max': 25000,
                'sum_dim_max': 150,
                'max_dim': 60,
                'price_max': 1500,
                'price_min': 0,
                'pickup_base': 23,
                'pickup_per_g': 0.017,
                'delivery_base': None,  # Not available
                'delivery_per_g': None,
            },
            {
                'name': 'UNI Small',  # K22
                'weight_min': 1,
                'weight_max': 2000,
                'sum_dim_max': 150,
                'max_dim': 60,
                'price_max': 7000,
                'price_min': 1501,
                'pickup_base': 16,
                'pickup_per_g': 0.025,
                'delivery_base': 19.5,
                'delivery_per_g': 0.025,
            },
            {
                'name': 'UNI Big',  # K29
                'weight_min': 2001,
                'weight_max': 25000,
                'sum_dim_max': 250,
                'max_dim': 150,
                'price_max': 7000,
                'price_min': 1501,
                'pickup_base': 36,
                'pickup_per_g': 0.017,
                'delivery_base': 39.5,
                'delivery_per_g': 0.017,
            },
            {
                'name': 'UNI Premium Small',  # K36
                'weight_min': 1,
                'weight_max': 5000,
                'sum_dim_max': 250,
                'max_dim': 150,
                'price_max': 250000,
                'price_min': 7001,
                'pickup_base': 22,
                'pickup_per_g': 0.025,
                'delivery_base': 25.5,
                'delivery_per_g': 0.025,
            },
            {
                'name': 'UNI Premium Big',  # K43
                'weight_min': 5001,
                'weight_max': 25000,
                'sum_dim_max': 310,
                'max_dim': 150,
                'price_max': 250000,
                'price_min': 7001,
                'pickup_base': 62,
                'pickup_per_g': 0.023,
                'delivery_base': 65.5,
                'delivery_per_g': 0.023,
            },
        ]
        
    def calculate_profit(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main profit calculation based on Excel formulas from 利润计算表.

        Excel formula (G11):
        利润 = A11 - B11 - C11 - D11 - E11 - F11
        Where:
        A11: 定价 (list_price) - selling price in RUB
        B11: 采购成本 (purchase_price) - cost price
        C11: 运费 (shipping_cost) - from UNI运费!SUM(K8,K15,K22,K29,K36,K43)
        D11: 贴单费 (label_fee) - fixed at 3
        E11: 平台佣金 (commission) = A11 * C9 (commission rate)
        F11: 杂费 (misc_fee) = A11 * 0.04

        Args:
            inputs: Dictionary containing calculation inputs

        Returns:
            Dictionary with calculation results
        """
        # Extract inputs
        list_price = inputs.get('list_price', 0.0)
        purchase_price = inputs.get('purchase_price', 0.0)
        commission_rate = inputs.get('commission_rate', 0.0)
        weight = inputs.get('weight', 0.0)
        length = inputs.get('length', 0.0)
        width = inputs.get('width', 0.0)
        height = inputs.get('height', 0.0)
        delivery_type = inputs.get('delivery_type', 'pickup')

        # Calculate components matching Excel formulas
        # C11: 运费 (shipping cost from UNI运费 sheet)
        shipping_cost = self._calculate_shipping(
            weight, (length, width, height), list_price, delivery_type
        )

        # D11: 贴单费 (fixed label fee)
        label_fee = self.constants['fixed_label_fee']

        # E11: 平台佣金 = A11 * commission_rate / 100
        commission_amount = list_price * commission_rate * self.constants['commission_rate_factor']

        # F11: 杂费 = A11 * 0.04
        misc_fee = list_price * self.constants['misc_fee_rate']

        # G11: 利润 = A11 - B11 - C11 - D11 - E11 - F11
        profit = list_price - purchase_price - shipping_cost - label_fee - commission_amount - misc_fee

        # Calculate profit rate (relative to purchase price)
        if purchase_price > 0:
            profit_rate = (profit / purchase_price) * 100
        else:
            profit_rate = 0.0

        return {
            'profit_amount': profit,
            'profit_rate': profit_rate,
            'shipping_cost': shipping_cost,
            'commission_amount': commission_amount,
            'label_fee': label_fee,
            'misc_fee': misc_fee,
            'is_loss': profit < 0,
            'breakdown': {
                'list_price': list_price,
                'purchase_price': purchase_price,
                'shipping_cost': shipping_cost,
                'label_fee': label_fee,
                'commission_amount': commission_amount,
                'misc_fee': misc_fee
            }
        }
        
    def _calculate_shipping(self, weight: float, dimensions: Tuple[float, float, float],
                          price: float, delivery_type: str) -> float:
        """
        Calculate shipping cost using the 6-channel logic from UNI运费 sheet.

        Excel Formula (K8, K15, K22, K29, K36, K43):
        =IF(AND(
            MAX($M$4:$M$6)<=V,      # max dimension <= limit
            SUM($M$4:$M$6)<=U,      # sum of dimensions <= limit
            $M$7<=W, $M$7>=X,       # price in range (RUB)
            $M$3>=S, $M$3<=T        # weight in range (g)
          ),
          IF($M$8="自提点",
             Y + $M$3*Z,            # pickup: base + weight * per_g
             AA + $M$3*AB           # delivery: base + weight * per_g
          ),
          ""
        )

        Final shipping = SUM of all matching channels (only one should match)

        Args:
            weight: Weight in grams
            dimensions: (length, width, height) in cm
            price: Product price in RUB
            delivery_type: 'pickup' or 'delivery' (or '自提点'/'送货上门')

        Returns:
            Shipping cost in RMB
        """
        length, width, height = dimensions
        max_dim = max(length, width, height)
        sum_dim = length + width + height

        # Normalize delivery type
        is_pickup = delivery_type in ('pickup', '自提点')

        # Find matching channel
        for channel in self.shipping_channels:
            # Check all conditions (AND logic from Excel)
            if not (max_dim <= channel['max_dim']):
                continue
            if not (sum_dim <= channel['sum_dim_max']):
                continue
            if not (price <= channel['price_max']):
                continue
            if not (price >= channel['price_min']):
                continue
            if not (weight >= channel['weight_min']):
                continue
            if not (weight <= channel['weight_max']):
                continue

            # All conditions matched - calculate shipping
            if is_pickup:
                base = channel['pickup_base']
                per_g = channel['pickup_per_g']
            else:
                base = channel['delivery_base']
                per_g = channel['delivery_per_g']

            # Check if delivery is available for this channel
            if base is None or per_g is None:
                # Delivery not available, fall back to pickup
                base = channel['pickup_base']
                per_g = channel['pickup_per_g']

            shipping_cost = base + weight * per_g
            return shipping_cost

        # No matching channel found - use default estimate
        # This shouldn't happen if inputs are valid
        return 20.0 if is_pickup else 25.0
        
    def calculate_cell(self, sheet: str, cell: str, inputs: Dict[str, Any]) -> Any:
        """
        Calculate a specific cell value
        
        Args:
            sheet: Sheet name
            cell: Cell reference
            inputs: Calculation inputs
            
        Returns:
            Calculated value
        """
        # Map specific cells to calculations
        cell_map = {
            ('利润计算表', 'G11'): lambda: self.calculate_profit(inputs)['profit_amount'],
            ('利润计算表', 'C11'): lambda: self._calculate_shipping(
                inputs.get('weight', 0),
                (inputs.get('length', 0), inputs.get('width', 0), inputs.get('height', 0)),
                inputs.get('list_price', 0),
                inputs.get('delivery_type', 'pickup')
            ),
            ('利润计算表', 'E11'): lambda: (
                inputs.get('list_price', 0) * 
                inputs.get('commission_rate', 0) * 
                self.constants['commission_rate_factor']
            ),
        }
        
        key = (sheet, cell)
        if key in cell_map:
            return cell_map[key]()
        else:
            raise ValueError(f"Unknown cell reference: {sheet}!{cell}")
            
    def get_formula(self, sheet: str, cell: str) -> str:
        """
        Get the Excel formula for a specific cell
        
        Args:
            sheet: Sheet name  
            cell: Cell reference
            
        Returns:
            Excel formula as string
        """
        formulas = {
            ('利润计算表', 'G11'): '=A11-B11-C11-D11-E11-F11',
            ('利润计算表', 'C11'): '=VLOOKUP(weight,UNI运费!A:D,IF(delivery_type="pickup",3,4),TRUE)',
            ('利润计算表', 'E11'): '=A11*commission_rate/100',
            ('利润计算表', 'D11'): '=2',  # Fixed label fee
        }
        
        key = (sheet, cell)
        return formulas.get(key, "")