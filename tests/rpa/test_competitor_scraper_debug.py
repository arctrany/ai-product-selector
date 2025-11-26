"""
跟卖店铺抓取器调试测试

基于用户提供的真实HTML结构，验证选择器配置是否能正确提取所有跟卖店铺
"""

import sys
import logging
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

from common.scrapers.competitor_scraper import CompetitorScraper
from common.config.ozon_selectors_config import get_ozon_selectors_config
from tests.rpa.base_scraper_test import BaseScraperTest

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 用户提供的真实HTML结构
REAL_HTML = """
<div data-widget="modalLayout" class="n1"><div class="b6 n3" data-widget="blockVertical" style="width: auto;"><div class="pdp_a6b" data-widget="webSellerList"><div id="seller-list" class="pdp_k1b"><h3 class="pdp_bk2">
    Другие предложения от продавцов на Ozon.ru
  </h3> <div class="pdp_b2k"><div class="pdp_kb2"><!----> <div class="pdp_b5j"><div class="pdp_jb5 pdp_j5b"><a href="https://www.ozon.ru/seller/schastlivyy-magazin-2279819/" class="pdp_ea2 pdp_ae3"><img loading="lazy" fetchpriority="low" src="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/JA/K4/wc100/JAK4sPfsoPHlvQUOfLke9e7ovGWyyFM3.png" srcset="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/JA/K4/wc200/JAK4sPfsoPHlvQUOfLke9e7ovGWyyFM3.png 2x" crossorigin="anonymous" class="pdp_e3a b95_3_3-a"></a></div> <div class="pdp_jb5 pdp_b6j"><div class="pdp_ae4"><div class="pdp_a4e"><div class="pdp_ea4"><a title="Счастливый магазин" href="https://www.ozon.ru/seller/schastlivyy-magazin-2279819/" class="pdp_ae5">Счастливый магазин</a><div class="ea5_3_9-a pdp_a3b pdp_ea5"><button aria-label="" class="ga5_3_7-a"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" class="ga5_3_7-a0" style="color: var(--graphicQuaternary);"><path fill="currentColor" d="M8 0c4.964 0 8 3.036 8 8s-3.036 8-8 8-8-3.036-8-8 3.036-8 8-8m-.889 11.556a.889.889 0 0 0 1.778 0V8A.889.889 0 0 0 7.11 8zM8.89 4.444a.889.889 0 1 0-1.778 0 .889.889 0 0 0 1.778 0"></path></svg></button> </div></div></div><div class="pdp_a5e">Перейти в магазин</div></div> <!----></div> <div class="pdp_jb5 pdp_jb6"><div class="pdp_bk0"><div><div class="pdp_b1k">14\u2009482\u2009₽</div><div class="pdp_kb1">с Ozon Картой</div></div></div></div> <div class="pdp_jb5 pdp_bj6"><ul class=""><li><div class="pdp_b3j pdp_jb4"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="pdp_bj4"><path fill="currentColor" d="M20.657 3.32a1.12 1.12 0 0 0-1.573.014l-4.371 4.37a1 1 0 0 1-.909.272l-9.589-1.97a.178.178 0 0 0-.098.34l7.238 2.715a1 1 0 0 1 .418 1.576L6.77 16.64a1 1 0 0 1-1.216.254l-.488-.244 2.286 2.286-.244-.489a1 1 0 0 1 .254-1.215l6.003-5.002a1 1 0 0 1 1.577.418l2.714 7.234a.182.182 0 0 0 .349-.1L16.027 10.2a1 1 0 0 1 .272-.91l4.372-4.369a1.12 1.12 0 0 0-.014-1.6m-2.988-1.4a3.123 3.123 0 0 1 4.416 4.415l-3.99 3.988 1.87 9.054a2.182 2.182 0 0 1-4.182 1.207l-2.22-5.916-4.311 3.592.013.027a2.96 2.96 0 0 1-.555 3.42 1 1 0 0 1-1.415 0l-5.002-5.001a1 1 0 0 1 0-1.415 2.96 2.96 0 0 1 3.42-.555l.028.014 3.593-4.31-5.92-2.22a2.179 2.179 0 0 1 1.204-4.174l9.061 1.862z"></path></svg><div class="pdp_jb3"><span class="q6b3_0_2-a"><span>Доставим 6 декабря</span></span></div></div></li></ul> <!----></div> <div class="pdp_jb5 pdp_j6b"><button class="b25_4_4-a0 b25_4_4-b6 b25_4_4-b2"><div class="b25_4_4-a2"><div class="b25_4_4-a9 tsBodyControl400Small">В корзину</div></div><div class="b25_4_4-a"></div></button></div></div></div><div class="pdp_kb2"><!----> <div class="pdp_b5j"><div class="pdp_jb5 pdp_j5b"><a href="https://www.ozon.ru/seller/good-and-excellent-12-1935225/" class="pdp_ea2 pdp_ae3"><img loading="lazy" fetchpriority="low" src="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/Bo/wS/wc100/BowSZjw4CZec383lXvD49oDn6AYBxLHI.png" srcset="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/Bo/wS/wc200/BowSZjw4CZec383lXvD49oDn6AYBxLHI.png 2x" crossorigin="anonymous" class="pdp_e3a b95_3_3-a"></a></div> <div class="pdp_jb5 pdp_b6j"><div class="pdp_ae4"><div class="pdp_a4e"><div class="pdp_ea4"><a title="Good and excellent 12" href="https://www.ozon.ru/seller/good-and-excellent-12-1935225/" class="pdp_ae5">Good and excellent 12</a><div class="ea5_3_9-a pdp_a3b pdp_ea5"><button aria-label="" class="ga5_3_7-a"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" class="ga5_3_7-a0" style="color: var(--graphicQuaternary);"><path fill="currentColor" d="M8 0c4.964 0 8 3.036 8 8s-3.036 8-8 8-8-3.036-8-8 3.036-8 8-8m-.889 11.556a.889.889 0 0 0 1.778 0V8A.889.889 0 0 0 7.11 8zM8.89 4.444a.889.889 0 1 0-1.778 0 .889.889 0 0 0 1.778 0"></path></svg></button> </div></div></div><div class="pdp_a5e">Перейти в магазин</div></div> <!----></div> <div class="pdp_jb5 pdp_jb6"><div class="pdp_bk0"><div><div class="pdp_b1k">14\u2009556\u2009₽</div><div class="pdp_kb1">с Ozon Картой</div></div></div></div> <div class="pdp_jb5 pdp_bj6"><ul class=""><li><div class="pdp_b3j pdp_jb4"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="pdp_bj4"><path fill="currentColor" d="M20.657 3.32a1.12 1.12 0 0 0-1.573.014l-4.371 4.37a1 1 0 0 1-.909.272l-9.589-1.97a.178.178 0 0 0-.098.34l7.238 2.715a1 1 0 0 1 .418 1.576L6.77 16.64a1 1 0 0 1-1.216.254l-.488-.244 2.286 2.286-.244-.489a1 1 0 0 1 .254-1.215l6.003-5.002a1 1 0 0 1 1.577.418l2.714 7.234a.182.182 0 0 0 .349-.1L16.027 10.2a1 1 0 0 1 .272-.91l4.372-4.369a1.12 1.12 0 0 0-.014-1.6m-2.988-1.4a3.123 3.123 0 0 1 4.416 4.415l-3.99 3.988 1.87 9.054a2.182 2.182 0 0 1-4.182 1.207l-2.22-5.916-4.311 3.592.013.027a2.96 2.96 0 0 1-.555 3.42 1 1 0 0 1-1.415 0l-5.002-5.001a1 1 0 0 1 0-1.415 2.96 2.96 0 0 1 3.42-.555l.028.014 3.593-4.31-5.92-2.22a2.179 2.179 0 0 1 1.204-4.174l9.061 1.862z"></path></svg><div class="pdp_jb3"><span class="q6b3_0_2-a"><span>Доставим 7 декабря</span></span></div></div></li></ul> <div class="pdp_b3j"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="pdp_bj4 pdp_b4j"><path fill="currentColor" d="m11 13.586 4.293-4.293a1 1 0 1 1 1.414 1.414l-5 5a.997.997 0 0 1-1.414 0l-3-3a1 1 0 1 1 1.414-1.414z"></path><path fill="currentColor" d="M1 12C1 5.925 5.925 1 12 1s11 4.925 11 11-4.925 11-11 11S1 18.075 1 12m11-9a9 9 0 1 0 0 18 9 9 0 0 0 0-18"></path></svg><div class="pdp_jb3">Проверенный продавец бренда</div></div></div> <div class="pdp_jb5 pdp_j6b"><button class="b25_4_4-a0 b25_4_4-b6 b25_4_4-b2"><div class="b25_4_4-a2"><div class="b25_4_4-a9 tsBodyControl400Small">В корзину</div></div><div class="b25_4_4-a"></div></button></div></div></div><div class="pdp_kb2"><!----> <div class="pdp_b5j"><div class="pdp_jb5 pdp_j5b"><a href="https://www.ozon.ru/seller/new-vospominaniya-stranitsa-7-1812037/" class="pdp_ea2 pdp_ae3"><img loading="lazy" fetchpriority="low" src="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/uv/Tt/wc100/uvTtgmbKH8wbGSJ700JnKunbrlId2v4E.png" srcset="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/uv/Tt/wc200/uvTtgmbKH8wbGSJ700JnKunbrlId2v4E.png 2x" crossorigin="anonymous" class="pdp_e3a b95_3_3-a"></a></div> <div class="pdp_jb5 pdp_b6j"><div class="pdp_ae4"><div class="pdp_a4e"><div class="pdp_ea4"><a title="NEW Воспоминания Страница 7" href="https://www.ozon.ru/seller/new-vospominaniya-stranitsa-7-1812037/" class="pdp_ae5">NEW Воспоминания Страница 7</a><div class="ea5_3_9-a pdp_a3b pdp_ea5"><button aria-label="" class="ga5_3_7-a"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" class="ga5_3_7-a0" style="color: var(--graphicQuaternary);"><path fill="currentColor" d="M8 0c4.964 0 8 3.036 8 8s-3.036 8-8 8-8-3.036-8-8 3.036-8 8-8m-.889 11.556a.889.889 0 0 0 1.778 0V8A.889.889 0 0 0 7.11 8zM8.89 4.444a.889.889 0 1 0-1.778 0 .889.889 0 0 0 1.778 0"></path></svg></button> </div></div></div><div class="pdp_a5e">Перейти в магазин</div></div> <!----></div> <div class="pdp_jb5 pdp_jb6"><div class="pdp_bk0"><div><div class="pdp_b1k">14\u2009562\u2009₽</div><div class="pdp_kb1">с Ozon Картой</div></div></div></div> <div class="pdp_jb5 pdp_bj6"><ul class=""><li><div class="pdp_b3j pdp_jb4"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="pdp_bj4"><path fill="currentColor" d="M20.657 3.32a1.12 1.12 0 0 0-1.573.014l-4.371 4.37a1 1 0 0 1-.909.272l-9.589-1.97a.178.178 0 0 0-.098.34l7.238 2.715a1 1 0 0 1 .418 1.576L6.77 16.64a1 1 0 0 1-1.216.254l-.488-.244 2.286 2.286-.244-.489a1 1 0 0 1 .254-1.215l6.003-5.002a1 1 0 0 1 1.577.418l2.714 7.234a.182.182 0 0 0 .349-.1L16.027 10.2a1 1 0 0 1 .272-.91l4.372-4.369a1.12 1.12 0 0 0-.014-1.6m-2.988-1.4a3.123 3.123 0 0 1 4.416 4.415l-3.99 3.988 1.87 9.054a2.182 2.182 0 0 1-4.182 1.207l-2.22-5.916-4.311 3.592.013.027a2.96 2.96 0 0 1-.555 3.42 1 1 0 0 1-1.415 0l-5.002-5.001a1 1 0 0 1 0-1.415 2.96 2.96 0 0 1 3.42-.555l.028.014 3.593-4.31-5.92-2.22a2.179 2.179 0 0 1 1.204-4.174l9.061 1.862z"></path></svg><div class="pdp_jb3"><span class="q6b3_0_2-a"><span>Доставим 7 декабря</span></span></div></div></li></ul> <!----></div> <div class="pdp_jb5 pdp_j6b"><button class="b25_4_4-a0 b25_4_4-b6 b25_4_4-b2"><div class="b25_4_4-a2"><div class="b25_4_4-a9 tsBodyControl400Small">В корзину</div></div><div class="b25_4_4-a"></div></button></div></div></div><div class="pdp_kb2"><!----> <div class="pdp_b5j"><div class="pdp_jb5 pdp_j5b"><a href="https://www.ozon.ru/seller/original-quality-store-7-1894948/" class="pdp_ea2 pdp_ae3"><img loading="lazy" fetchpriority="low" src="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/aF/tC/wc100/aFtC6iug24GBMkZ9XEhi3qhQj6cewjGh.png" srcset="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/aF/tC/wc200/aFtC6iug24GBMkZ9XEhi3qhQj6cewjGh.png 2x" crossorigin="anonymous" class="pdp_e3a b95_3_3-a"></a></div> <div class="pdp_jb5 pdp_b6j"><div class="pdp_ae4"><div class="pdp_a4e"><div class="pdp_ea4"><a title="Original quality store 7" href="https://www.ozon.ru/seller/original-quality-store-7-1894948/" class="pdp_ae5">Original quality store 7</a><div class="ea5_3_9-a pdp_a3b pdp_ea5"><button aria-label="" class="ga5_3_7-a"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" class="ga5_3_7-a0" style="color: var(--graphicQuaternary);"><path fill="currentColor" d="M8 0c4.964 0 8 3.036 8 8s-3.036 8-8 8-8-3.036-8-8 3.036-8 8-8m-.889 11.556a.889.889 0 0 0 1.778 0V8A.889.889 0 0 0 7.11 8zM8.89 4.444a.889.889 0 1 0-1.778 0 .889.889 0 0 0 1.778 0"></path></svg></button> </div></div></div><div class="pdp_a5e">Перейти в магазин</div></div> <!----></div> <div class="pdp_jb5 pdp_jb6"><div class="pdp_bk0"><div><div class="pdp_b1k">14\u2009602\u2009₽</div><div class="pdp_kb1">с Ozon Картой</div></div></div></div> <div class="pdp_jb5 pdp_bj6"><ul class=""><li><div class="pdp_b3j pdp_jb4"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="pdp_bj4"><path fill="currentColor" d="M20.657 3.32a1.12 1.12 0 0 0-1.573.014l-4.371 4.37a1 1 0 0 1-.909.272l-9.589-1.97a.178.178 0 0 0-.098.34l7.238 2.715a1 1 0 0 1 .418 1.576L6.77 16.64a1 1 0 0 1-1.216.254l-.488-.244 2.286 2.286-.244-.489a1 1 0 0 1 .254-1.215l6.003-5.002a1 1 0 0 1 1.577.418l2.714 7.234a.182.182 0 0 0 .349-.1L16.027 10.2a1 1 0 0 1 .272-.91l4.372-4.369a1.12 1.12 0 0 0-.014-1.6m-2.988-1.4a3.123 3.123 0 0 1 4.416 4.415l-3.99 3.988 1.87 9.054a2.182 2.182 0 0 1-4.182 1.207l-2.22-5.916-4.311 3.592.013.027a2.96 2.96 0 0 1-.555 3.42 1 1 0 0 1-1.415 0l-5.002-5.001a1 1 0 0 1 0-1.415 2.96 2.96 0 0 1 3.42-.555l.028.014 3.593-4.31-5.92-2.22a2.179 2.179 0 0 1 1.204-4.174l9.061 1.862z"></path></svg><div class="pdp_jb3"><span class="q6b3_0_2-a"><span>Доставим 6 декабря</span></span></div></div></li></ul> <div class="pdp_b3j"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="pdp_bj4 pdp_b4j"><path fill="currentColor" d="m11 13.586 4.293-4.293a1 1 0 1 1 1.414 1.414l-5 5a.997.997 0 0 1-1.414 0l-3-3a1 1 0 1 1 1.414-1.414z"></path><path fill="currentColor" d="M1 12C1 5.925 5.925 1 12 1s11 4.925 11 11-4.925 11-11 11S1 18.075 1 12m11-9a9 9 0 1 0 0 18 9 9 0 0 0 0-18"></path></svg><div class="pdp_jb3">Проверенный продавец бренда</div></div></div> <div class="pdp_jb5 pdp_j6b"><button class="b25_4_4-a0 b25_4_4-b6 b25_4_4-b2"><div class="b25_4_4-a2"><div class="b25_4_4-a9 tsBodyControl400Small">В корзину</div></div><div class="b25_4_4-a"></div></button></div></div></div><div class="pdp_kb2"><!----> <div class="pdp_b5j"><div class="pdp_jb5 pdp_j5b"><a href="https://www.ozon.ru/seller/money-and-prosperity5-1806816/" class="pdp_ea2 pdp_ae3"><img loading="lazy" fetchpriority="low" src="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/04/L6/wc100/04L6532NpE8duAyAMGyDQYZTF7APfCgm.png" srcset="https://cdn1.ozonusercontent.com/s3/marketing-api/banners/04/L6/wc200/04L6532NpE8duAyAMGyDQYZTF7APfCgm.png 2x" crossorigin="anonymous" class="pdp_e3a b95_3_3-a"></a></div> <div class="pdp_jb5 pdp_b6j"><div class="pdp_ae4"><div class="pdp_a4e"><div class="pdp_ea4"><a title="Money and Prosperity5" href="https://www.ozon.ru/seller/money-and-prosperity5-1806816/" class="pdp_ae5">Money and Prosperity5</a><div class="ea5_3_9-a pdp_a3b pdp_ea5"><button aria-label="" class="ga5_3_7-a"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" class="ga5_3_7-a0" style="color: var(--graphicQuaternary);"><path fill="currentColor" d="M8 0c4.964 0 8 3.036 8 8s-3.036 8-8 8-8-3.036-8-8 3.036-8 8-8m-.889 11.556a.889.889 0 0 0 1.778 0V8A.889.889 0 0 0 7.11 8zM8.89 4.444a.889.889 0 1 0-1.778 0 .889.889 0 0 0 1.778 0"></path></svg></button> </div></div></div><div class="pdp_a5e">Перейти в магазин</div></div> <!----></div> <div class="pdp_jb5 pdp_jb6"><div class="pdp_bk0"><div><div class="pdp_b1k">14\u2009864\u2009₽</div><div class="pdp_kb1">с Ozon Картой</div></div></div></div> <div class="pdp_jb5 pdp_bj6"><ul class=""><li><div class="pdp_b3j pdp_jb4"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="pdp_bj4"><path fill="currentColor" d="M20.657 3.32a1.12 1.12 0 0 0-1.573.014l-4.371 4.37a1 1 0 0 1-.909.272l-9.589-1.97a.178.178 0 0 0-.098.34l7.238 2.715a1 1 0 0 1 .418 1.576L6.77 16.64a1 1 0 0 1-1.216.254l-.488-.244 2.286 2.286-.244-.489a1 1 0 0 1 .254-1.215l6.003-5.002a1 1 0 0 1 1.577.418l2.714 7.234a.182.182 0 0 0 .349-.1L16.027 10.2a1 1 0 0 1 .272-.91l4.372-4.369a1.12 1.12 0 0 0-.014-1.6m-2.988-1.4a3.123 3.123 0 0 1 4.416 4.415l-3.99 3.988 1.87 9.054a2.182 2.182 0 0 1-4.182 1.207l-2.22-5.916-4.311 3.592.013.027a2.96 2.96 0 0 1-.555 3.42 1 1 0 0 1-1.415 0l-5.002-5.001a1 1 0 0 1 0-1.415 2.96 2.96 0 0 1 3.42-.555l.028.014 3.593-4.31-5.92-2.22a2.179 2.179 0 0 1 1.204-4.174l9.061 1.862z"></path></svg><div class="pdp_jb3"><span class="q6b3_0_2-a"><span>Доставим 7 декабря</span></span></div></div></li></ul> <!----></div> <div class="pdp_jb5 pdp_j6b"><button class="b25_4_4-a0 b25_4_4-b6 b25_4_4-b2"><div class="b25_4_4-a2"><div class="b25_4_4-a9 tsBodyControl400Small">В корзину</div></div><div class="b25_4_4-a"></div></button></div></div></div></div> <button class="b25_4_4-a0 b25_4_4-b7 b25_4_4-a5"><div class="b25_4_4-a2"><div class="b25_4_4-a9 tsBodyControl500Medium">Еще 7</div></div><div class="b25_4_4-a"></div></button></div><!----></div></div></div>
"""

def test_competitor_extraction():
    """测试跟卖店铺信息提取 - 同步版本"""
    print("🔍 开始测试跟卖店铺信息提取...")

    # 创建抓取器实例
    scraper = CompetitorScraper()

    # 测试HTML解析 - 现在使用同步方法
    competitors = scraper.extract_competitors_from_content(REAL_HTML, max_competitors=10)
    
    print(f"\n📊 提取结果:")
    print(f"🎯 找到跟卖店铺数量: {len(competitors)}")
    
    if competitors:
        print(f"\n📋 跟卖店铺详情:")
        for i, competitor in enumerate(competitors, 1):
            print(f"   {i}. {competitor.get('store_name', 'N/A')} - {competitor.get('price', 'N/A')}₽ (ID: {competitor.get('store_id', 'N/A')})")
    else:
        print("❌ 未提取到任何跟卖店铺")
    
    # 验证预期结果
    expected_stores = [
        "Счастливый магазин",
        "Good and excellent 12", 
        "NEW Воспоминания Страница 7",
        "Original quality store 7",
        "Money and Prosperity5"
    ]
    
    expected_prices = [14482.0, 14556.0, 14562.0, 14602.0, 14864.0]
    
    print(f"\n🎯 验证结果:")
    if len(competitors) == 5:
        print("✅ 店铺数量正确：5个")
    else:
        print(f"❌ 店铺数量错误：期望5个，实际{len(competitors)}个")
    
    # 验证店铺名称
    extracted_names = [c.get('store_name', '') for c in competitors]
    for expected_name in expected_stores:
        if expected_name in extracted_names:
            print(f"✅ 找到店铺：{expected_name}")
        else:
            print(f"❌ 缺失店铺：{expected_name}")
    
    # 验证价格
    extracted_prices = [c.get('price') for c in competitors if c.get('price')]
    for expected_price in expected_prices:
        if expected_price in extracted_prices:
            print(f"✅ 找到价格：{expected_price}₽")
        else:
            print(f"❌ 缺失价格：{expected_price}₽")
    
    return len(competitors) == 5

def test_selector_matching():
    """测试选择器匹配"""
    print("\n🔍 测试选择器匹配...")
    
    soup = BeautifulSoup(REAL_HTML, 'html.parser')
    config = get_ozon_selectors_config()
    
    # 测试容器选择器
    print(f"\n📦 测试容器选择器:")
    for selector in config.competitor_area_selectors:
        try:
            container = soup.select_one(selector)
            if container:
                print(f"✅ 容器选择器有效: {selector}")
                break
        except Exception as e:
            print(f"❌ 容器选择器失败: {selector} - {e}")
    
    # 测试店铺元素选择器
    print(f"\n🏪 测试店铺元素选择器:")
    # 使用配置系统中的容器选择器
    container = None
    for container_selector in config.competitor_area_selectors:
        container = soup.select_one(container_selector)
        if container:
            print(f"✅ 使用容器选择器: {container_selector}")
            break

    if container:
        for selector in config.competitor_element_selectors:
            try:
                elements = container.select(selector)
                if elements:
                    print(f"✅ 店铺元素选择器有效: {selector} (找到{len(elements)}个)")
                    if len(elements) == 5:
                        print(f"🎯 完美匹配！找到所有5个店铺")
                        break
            except Exception as e:
                print(f"❌ 店铺元素选择器失败: {selector} - {e}")
    
    # 测试店铺名称选择器
    print(f"\n🏷️ 测试店铺名称选择器:")
    # 使用配置系统中的元素选择器
    shop_elements = []
    if container:
        for element_selector in config.competitor_element_selectors:
            elements = container.select(element_selector)
            if elements:
                shop_elements.extend(elements)
                print(f"✅ 使用元素选择器: {element_selector} (找到{len(elements)}个)")
                break

    if shop_elements:
        for selector in config.store_name_selectors:
            found_names = []
            for element in shop_elements:
                try:
                    name_element = element.select_one(selector)
                    if name_element:
                        name = name_element.get_text(strip=True)
                        if name:
                            found_names.append(name)
                except:
                    continue
            if found_names:
                print(f"✅ 店铺名称选择器有效: {selector} (找到{len(found_names)}个名称)")
                if len(found_names) == 5:
                    print(f"🎯 完美匹配！找到所有5个店铺名称: {found_names}")
                    break
    
    # 测试价格选择器
    print(f"\n💰 测试价格选择器:")
    if shop_elements:
        for selector in config.store_price_selectors:
            found_prices = []
            for element in shop_elements:
                try:
                    price_element = element.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text(strip=True)
                        if price_text and '₽' in price_text:
                            found_prices.append(price_text)
                except:
                    continue
            if found_prices:
                print(f"✅ 价格选择器有效: {selector} (找到{len(found_prices)}个价格)")
                if len(found_prices) == 5:
                    print(f"🎯 完美匹配！找到所有5个价格: {found_prices}")
                    break

class TestCompetitorScraperDebug(BaseScraperTest):
    """CompetitorScraper调试测试 - 使用统一测试基类"""
    
    def test_competitor_extraction_from_html(self):
        """测试从HTML提取跟卖店铺信息"""
        scraper = CompetitorScraper()
        competitors = scraper.extract_competitors_from_content(REAL_HTML, max_competitors=10)
        
        # 使用基类的断言方法
        self.assertIsNotNone(competitors, "提取的跟卖店铺列表不应为None")
        self.assertEqual(len(competitors), 5, f"期望提取5个跟卖店铺，实际提取{len(competitors)}个")
        
        # 验证店铺名称
        expected_stores = [
            "Счастливый магазин",
            "Good and excellent 12", 
            "NEW Воспоминания Страница 7",
            "Original quality store 7",
            "Money and Prosperity5"
        ]
        extracted_names = [c.get('store_name', '') for c in competitors]
        for expected_name in expected_stores:
            self.assertIn(expected_name, extracted_names, f"缺失店铺: {expected_name}")
        
        # 验证价格
        expected_prices = [14482.0, 14556.0, 14562.0, 14602.0, 14864.0]
        extracted_prices = [c.get('price') for c in competitors if c.get('price')]
        for expected_price in expected_prices:
            self.assertIn(expected_price, extracted_prices, f"缺失价格: {expected_price}₽")
    
    def test_selector_configuration(self):
        """测试选择器配置的有效性"""
        soup = BeautifulSoup(REAL_HTML, 'html.parser')
        config = get_ozon_selectors_config()
        
        # 测试容器选择器
        container = None
        for selector in config.competitor_area_selectors:
            container = soup.select_one(selector)
            if container:
                break
        
        self.assertIsNotNone(container, "应该能找到跟卖容器")
        
        # 测试店铺元素选择器
        elements = []
        for selector in config.competitor_element_selectors:
            elements = container.select(selector)
            if elements:
                break
        
        self.assertEqual(len(elements), 5, f"应该找到5个店铺元素，实际找到{len(elements)}个")


def main():
    """主测试函数 - 同步版本"""
    print("🚀 开始跟卖店铺抓取器调试测试")
    print("=" * 60)

    # 测试选择器匹配
    test_selector_matching()

    print("\n" + "=" * 60)

    # 测试店铺信息提取
    success = test_competitor_extraction()

    print("\n" + "=" * 60)
    print(f"🎉 测试完成！结果: {'✅ 成功' if success else '❌ 失败'}")

    return success

if __name__ == "__main__":
    main()
