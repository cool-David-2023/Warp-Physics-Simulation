"""
Simulation Panel - 模擬參數面板
包含 Collection 選擇、UIList、物件材質參數
"""

import bpy
from .. import config


# ============================================================
# UIList - 顯示 Collection 內的物件
# ============================================================

class WARP_UL_ObjectList(bpy.types.UIList):
    """物件列表 UIList"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """繪製列表項目"""
        obj = item
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            
            # Enabled toggle
            row.prop(obj, "warp_enabled", text="", icon='CHECKBOX_HLT' if obj.warp_enabled else 'CHECKBOX_DEHLT', emboss=False)
            
            # 物件名稱
            row.label(text=obj.name, icon='MESH_DATA')
            
            # Viewport visibility toggle
            row.prop(obj, "hide_viewport", text="", emboss=False)
        
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MESH_DATA')


# ============================================================
# Panel
# ============================================================

class WARP_PT_SimulationPanel(bpy.types.Panel):
    """Simulation Parameters 面板"""
    
    bl_label = "Simulation Parameters"
    bl_idname = "WARP_PT_simulation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 2
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Collection 選擇器
        self._draw_collection_selector(layout, scene)
        
        layout.separator()
        
        # Objects in Collection (UIList)
        self._draw_object_list(layout, scene, context)
        
        layout.separator()
        
        # 選中物件的材質參數
        self._draw_material_properties(layout, scene, context)
    
    def _draw_collection_selector(self, layout, scene):
        """繪製 Collection 選擇器"""
        box = layout.box()
        col = box.column(align=True)
        
        col.label(text="Collection:", icon='OUTLINER_COLLECTION')
        col.prop(scene, "warp_collection", text="")
    
    def _draw_object_list(self, layout, scene, context):
        """繪製物件列表"""
        box = layout.box()
        col = box.column(align=True)
        
        col.label(text="Objects in Collection:", icon='OBJECT_DATA')
        
        collection = scene.warp_collection
        
        if collection is None:
            col.label(text="No collection selected", icon='ERROR')
            return
        
        # UIList
        row = col.row()
        row.template_list(
            "WARP_UL_ObjectList",
            "",
            collection,
            "all_objects",
            scene,
            "warp_active_object_index",
            rows=5
        )
    
    def _draw_material_properties(self, layout, scene, context):
        """繪製選中物件的材質參數"""
        box = layout.box()
        
        collection = scene.warp_collection
        if collection is None:
            box.label(text="No collection selected", icon='INFO')
            return
        
        objects = collection.all_objects
        if len(objects) == 0:
            box.label(text="Collection is empty", icon='INFO')
            return
        
        active_idx = scene.warp_active_object_index
        if active_idx < 0 or active_idx >= len(objects):
            box.label(text="No object selected", icon='INFO')
            return
        
        obj = objects[active_idx]
        
        # 標題 + Material Library
        row = box.row(align=True)
        row.label(text=f"Material for: {obj.name}", icon='MATERIAL')
        row.popover(panel="WARP_PT_MaterialLibrary", text="", icon='PRESET')
        
        col = box.column(align=True)
        
        # === Material Properties ===
        row = col.row()
        row.prop(
            scene,
            "warp_show_material",
            icon='TRIA_DOWN' if scene.warp_show_material else 'TRIA_RIGHT',
            text="Material Properties",
            emboss=False
        )
        
        if scene.warp_show_material:
            subcol = col.column(align=True)
            subcol.prop(obj, '["warp_density"]', text="Density (kg/m³)")
            subcol.prop(obj, '["warp_k_mu"]', text="Shear Modulus")
            subcol.prop(obj, '["warp_k_lambda"]', text="Bulk Modulus")
            subcol.prop(obj, '["warp_k_damp"]', text="Damping")


# ============================================================
# Material Library Popover
# ============================================================

class WARP_PT_MaterialLibrary(bpy.types.Panel):
    """Material Library Popover"""
    
    bl_label = "Material Library"
    bl_idname = "WARP_PT_MaterialLibrary"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        collection = scene.warp_collection
        if collection is None:
            layout.label(text="No collection", icon='ERROR')
            return
        
        objects = collection.all_objects
        if len(objects) == 0:
            layout.label(text="No objects", icon='ERROR')
            return
        
        active_idx = scene.warp_active_object_index
        if active_idx < 0 or active_idx >= len(objects):
            layout.label(text="No object selected", icon='ERROR')
            return
        
        obj = objects[active_idx]
        
        # 預設按鈕
        col = layout.column(align=True)
        
        for preset_key, preset_data in config.PRESETS.items():
            preset_name = preset_data['name'].split('(')[0].strip()
            op = col.operator("warp.apply_preset_to_object", text=preset_name, icon='MATERIAL')
            op.preset = preset_key


def register():
    """註冊屬性"""
    Scene = bpy.types.Scene
    Object = bpy.types.Object
    
    # === Collection 選擇器 ===
    Scene.warp_collection = bpy.props.PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
        description="Collection containing simulation objects"
    )
    
    # === UIList 選中索引 ===
    Scene.warp_active_object_index = bpy.props.IntProperty(
        name="Active Object Index",
        default=0
    )
    
    # === UI 折疊控制 ===
    Scene.warp_show_material = bpy.props.BoolProperty(
        name="Show Material",
        default=True
    )
    
    Scene.warp_show_contact = bpy.props.BoolProperty(
        name="Show Contact",
        default=False
    )
    
    # === 物件屬性：啟用/禁用 ===
    Object.warp_enabled = bpy.props.BoolProperty(
        name="Enabled",
        description="Include this object in simulation",
        default=True
    )
    
    # === 物件材質屬性（Custom Properties 在物件創建時初始化） ===
    # 這些屬性由 initialize_object_material() 動態創建


def unregister():
    """移除屬性"""
    Scene = bpy.types.Scene
    Object = bpy.types.Object
    
    del Scene.warp_collection
    del Scene.warp_active_object_index
    del Scene.warp_show_material
    del Scene.warp_show_contact
    del Object.warp_enabled