"""
速率限制器 — 防止單一用戶無限消耗資源。
使用記憶體滑動視窗（重啟後重置，適合單一 worker 的免費方案）。
"""

import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# 設定：每 60 秒最多 10 則訊息
WINDOW_SECONDS = 60
MAX_REQUESTS = 10

_user_timestamps: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(user_id: str) -> bool:
    """
    回傳 True 表示此用戶已超過速率限制，應拒絕請求。
    回傳 False 表示允許通過，並記錄此次請求時間。
    """
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    # 清除視窗外的舊紀錄
    timestamps = _user_timestamps[user_id]
    _user_timestamps[user_id] = [t for t in timestamps if t > cutoff]

    if len(_user_timestamps[user_id]) >= MAX_REQUESTS:
        logger.warning("Rate limit hit: user=%s requests=%d", user_id, len(_user_timestamps[user_id]))
        return True

    _user_timestamps[user_id].append(now)
    return False
