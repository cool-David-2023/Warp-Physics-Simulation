"""
材質預設操作器 - 套用預設到選中物件
"""

import bpy
from .. import config


class WARP_OT_ApplyPresetToObject(bpy.types.Operator):
    """套用材質預設到當前選中物件"""
    
    bl_idname = "warp.apply_preset_to_object"
    bl_label = "Apply Preset"
    bl_description = "Apply material preset to selected object"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset: bpy.props.EnumProperty(
        name="Preset",
        items=[
            ('SOFT_RUBBER', '軟橡膠', 'Soft rubber material'),
            ('HARD_RUBBER', '硬橡膠', 'Hard rubber material'),
            ('JELLY', '果凍', 'Jelly-like material'),
            ('SOFT_FOAM', '軟泡棉', 'Soft foam material'),
            ('STIFF', '堅硬', 'Stiff material'),
        ]
    )
    
    def execute(self, context):
        """套用預設"""
        # 獲取當前選中物件
        collection = context.scene.warp_collection
        if collection is None:
            self.report({'ERROR'}, "無 Collection")
            return {'CANCELLED'}
        
        objects = collection.all_objects
        if len(objects) == 0:
            self.report({'ERROR'}, "Collection 為空")
            return {'CANCELLED'}
        
        active_idx = context.scene.warp_active_object_index
        if active_idx < 0 or active_idx >= len(objects):
            self.report({'ERROR'}, "無選中物件")
            return {'CANCELLED'}
        
        obj = objects[active_idx]
        
        # 套用預設
        success = config.apply_preset_to_object(obj, self.preset)
        
        if success:
            preset_name = config.PRESETS[self.preset]['name']
            print(f"✅ 已套用預設: {preset_name} → {obj.name}")
            self.report({'INFO'}, f"已套用: {preset_name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "套用失敗")
            return {'CANCELLED'}