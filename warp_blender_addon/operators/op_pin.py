"""
Pin 功能操作器 - 固定粒子控制（未來實作）
"""

import bpy
from .. import config


class WARP_OT_InitPinBottom(bpy.types.Operator):
    """初始化模型並固定底部粒子"""
    
    bl_idname = "warp.init_pin_bottom"
    bl_label = "Initialize (Pin Bottom)"
    bl_description = "Create model with bottom particles pinned"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        self.report({'WARNING'}, "Pin 功能尚未實作")
        return {'CANCELLED'}


class WARP_OT_InitPinTop(bpy.types.Operator):
    """初始化模型並固定頂部粒子"""
    
    bl_idname = "warp.init_pin_top"
    bl_label = "Initialize (Pin Top)"
    bl_description = "Create model with top particles pinned"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        self.report({'WARNING'}, "Pin 功能尚未實作")
        return {'CANCELLED'}


class WARP_OT_UpdatePinController(bpy.types.Operator):
    """更新 Pin 控制器（用於關鍵幀動畫）"""
    
    bl_idname = "warp.update_pin_controller"
    bl_label = "Update Pin Controller"
    bl_description = "Update pinned particles from controller object"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        self.report({'WARNING'}, "Pin 功能尚未實作")
        return {'CANCELLED'}


# 註：這些類別暫時不加入 __init__.py 的 __all__
# 等實作完成後再啟用