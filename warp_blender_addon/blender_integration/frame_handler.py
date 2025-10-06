"""
時間軸處理器 - 負責在時間軸播放時更新模擬
"""

import bpy
from .. import config
from ..core.cache_manager import CacheManager
from .mesh_builder import update_wireframe_mesh


# 全域 Handler 引用
_frame_handler = None


def update_from_cache(scene):
    """
    從快取更新線框（時間軸回調函數）
    
    Args:
        scene: Blender 場景物件
    """
    # 檢查快取狀態
    if not config.cache_info.get('baked', False):
        return
    
    if config.wireframe_object is None:
        return
    
    # 獲取當前幀
    frame = scene.frame_current
    
    # 檢查幀範圍
    frame_start = config.cache_info.get('frame_start', 1)
    frame_end = config.cache_info.get('frame_end', 250)
    
    if frame < frame_start or frame > frame_end:
        return
    
    try:
        # 載入該幀的位置數據
        cache_mgr = CacheManager()
        positions_warp = cache_mgr.load_frame(frame)
        
        if positions_warp is not None:
            # 更新線框網格
            update_wireframe_mesh(config.wireframe_object, positions_warp)
    
    except Exception as e:
        # 靜默失敗，避免阻塞時間軸播放
        print(f"⚠️ 更新幀 {frame} 失敗: {e}")


def register_frame_handler():
    """註冊時間軸更新 Handler"""
    global _frame_handler
    
    # 先移除舊的 Handler（避免重複註冊）
    unregister_frame_handler()
    
    # 註冊新 Handler
    _frame_handler = update_from_cache
    bpy.app.handlers.frame_change_pre.append(_frame_handler)
    
    print("✅ Frame Handler 已註冊")


def unregister_frame_handler():
    """移除時間軸更新 Handler"""
    global _frame_handler
    
    if _frame_handler is not None:
        # 檢查是否在 handlers 列表中
        if _frame_handler in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(_frame_handler)
            print("✅ Frame Handler 已移除")
        
        _frame_handler = None


def get_handler_status():
    """
    獲取 Handler 狀態
    
    Returns:
        dict: Handler 狀態資訊
    """
    return {
        'registered': _frame_handler is not None,
        'handler_count': len(bpy.app.handlers.frame_change_pre),
        'cache_baked': config.cache_info.get('baked', False),
    }


def force_update_current_frame():
    """強制更新當前幀（手動觸發）"""
    scene = bpy.context.scene
    update_from_cache(scene)
    print(f"✅ 已強制更新幀 {scene.frame_current}")


# 註：也可以使用 frame_change_post 而非 frame_change_pre
# frame_change_pre: 在幀改變前觸發（推薦用於更新顯示）
# frame_change_post: 在幀改變後觸發