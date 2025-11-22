# Change: 将类目黑名单配置从用户数据迁移到系统配置

## Why
当前类目黑名单配置 (`category_blacklist`) 通过 `--data` 参数（用户数据文件）传入，但这是系统级别的过滤规则，不应该由每个用户单独配置。将其迁移到 `--config` 参数（系统配置文件）的 `selector_filter` 配置中，可以：

1. **更清晰的配置分离**：用户数据 (`--data`) 专注于业务参数（如利润率、重量范围等），系统配置 (`--config`) 专注于系统级规则（如类目黑名单）
2. **统一管理**：类目黑名单作为系统级规则，应该由系统管理员统一配置，而不是每个用户都需要配置
3. **简化用户配置**：用户不再需要在自己的数据文件中维护类目黑名单列表
4. **向后兼容**：保留对旧配置的支持，但标记为废弃
5. **统一命名规范**：遵循 `item_**_filter`（商品级别）和 `store_**_filter`（店铺级别）的命名规范

## What Changes
- 重命名 `StoreFilterConfig` → `SelectorFilterConfig`
- 在 `SelectorFilterConfig` 中添加 `item_category_blacklist` 字段（商品级别的类目黑名单）
- 更新 `FilterManager` 从系统配置的 `selector_filter.item_category_blacklist` 读取类目黑名单
- 更新 `cli/main.py` 中的废弃字段警告逻辑
- 更新配置模板生成命令，移除 `category_blacklist` 字段
- 更新所有引用 `store_filter` 的代码改为 `selector_filter`
- 更新测试以反映新的配置方式
- 更新文档说明新的配置方式和命名规范

## Impact
- **Affected specs**: `store-filtering`, `cli`
- **Affected code**: 
  - `common/config.py` - 需要重命名 `StoreFilterConfig` → `SelectorFilterConfig`，添加 `item_category_blacklist`
  - `common/scrapers/filter_manager.py` - 需要更新读取配置的方式
  - `cli/main.py` - 需要更新废弃字段处理和配置引用
  - `cli/models.py` - 可能需要移除 `category_blacklist` 字段
  - `good_store_selector.py` - 需要更新配置引用
  - `tests/test_product_filter.py` - 需要更新测试
- **Breaking changes**: 配置文件结构变更（`store_filter` → `selector_filter`），但保留向后兼容性
- **Migration**: 
  1. 用户需要将 `category_blacklist` 从 `--data` 文件迁移到 `--config` 文件的 `selector_filter.item_category_blacklist` 中
  2. 系统配置文件需要将 `store_filter` 重命名为 `selector_filter`
