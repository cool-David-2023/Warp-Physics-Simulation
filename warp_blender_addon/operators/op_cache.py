"""
快取管理操作器 - 清除和載入快取
"""

import bpy
from .. import config
from ..core.cache_manager import CacheManager
from ..blender_integration.frame_handler import register_frame_handler, unregister_frame_handler


class WARP_OT_ClearCache(bpy.types.Operator):
    """清除 Warp 模擬快取"""
    
    bl_idname = "warp.clear_cache"
    bl_label = "Clear Cache"
    bl_description = "Delete all cached simulation data"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        """執行清除快取"""
        try:
            if config.cache_dir is None:
                self.report({'WARNING'}, "無快取目錄")
                return {'CANCELLED'}
            
            # 清除快取檔案
            cache_mgr = CacheManager()
            cache_mgr.clear_cache()
            
            # 重置快取狀態
            config.cache_info['baked'] = False
            
            # 移除時間軸處理器
            unregister_frame_handler()
            
            print("✅ 快取已清除")
            self.report({'INFO'}, "快取已清除")
            return {'FINISHED'}
            
        except Exception as e:
            print(f"❌ 清除快取失敗: {e}")
            self.report({'ERROR'}, f"清除失敗: {str(e)}")
            return {'CANCELLED'}


class WARP_OT_LoadCache(bpy.types.Operator):
    """載入現有的 Warp 模擬快取"""
    
    bl_idname = "warp.load_cache"
    bl_label = "Load Cache"
    bl_description = "Load existing simulation cache from disk"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        """執行載入快取"""
        try:
            # 獲取快取目錄
            cache_mgr = CacheManager()
            
            # 載入快取元資訊
            loaded_info = cache_mgr.load_cache_info()
            
            if loaded_info is None or not loaded_info.get('baked'):
                self.report({'WARNING'}, "找不到有效快取")
                return {'CANCELLED'}
            
            # 更新全域快取資訊
            config.cache_info.update(loaded_info)
            
            # 註冊時間軸處理器
            register_frame_handler()
            
            # 設置時間軸到快取起始幀
            context.scene.frame_set(config.cache_info['frame_start'])
            
            print(f"✅ 快取已載入: 幀 {config.cache_info['frame_start']}-{config.cache_info['frame_end']}")
            
            self.report(
                {'INFO'},
                f"快取已載入 ({config.cache_info['frame_start']}-{config.cache_info['frame_end']})"
            )
            return {'FINISHED'}
            
        except Exception as e:
            print(f"❌ 載入快取失敗: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"載入失敗: {str(e)}")
            return {'CANCELLED'}