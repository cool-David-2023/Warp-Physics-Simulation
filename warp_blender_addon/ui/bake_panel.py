"""
Bake Panel - Bake 控制與狀態顯示
包含模擬品質、初始化、Bake、快取狀態
"""

import bpy
from .. import config


class WARP_PT_BakePanel(bpy.types.Panel):
    """Bake Control 面板"""
    
    bl_label = "Bake Control"
    bl_idname = "WARP_PT_bake_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 3
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 模擬品質
        self._draw_simulation_quality(layout, scene)
        
        layout.separator()
        
        # 初始化
        self._draw_initialization(layout, scene)
        
        layout.separator()
        
        # Bake 控制
        self._draw_bake_control(layout)
        
        layout.separator()
        
        # 快取狀態
        self._draw_cache_status(layout)
    
    def _draw_simulation_quality(self, layout, scene):
        """繪製模擬品質設定"""
        box = layout.box()
        col = box.column(align=True)
        
        col.label(text="Simulation Quality:", icon='SETTINGS')
        col.prop(scene, "warp_sim_substeps", text="Substeps per Frame")
        
        # 顯示計算的時間步長
        fps = scene.render.fps
        substeps = scene.warp_sim_substeps
        dt = 1.0 / (fps * substeps)
        
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text=f"dt ≈ {dt:.6f}s", icon='TIME')
        
        col.separator()
        
        # === 全域接觸參數 ===
        col.label(text="Contact Settings (Global):", icon='PHYSICS')
        subcol = col.column(align=True)
        subcol.prop(scene, "warp_contact_ke", text="Contact Stiffness")
        subcol.prop(scene, "warp_contact_kd", text="Contact Damping")
        subcol.prop(scene, "warp_contact_kf", text="Friction Stiffness")
        subcol.prop(scene, "warp_contact_mu", text="Friction Coefficient")
    
    def _draw_initialization(self, layout, scene):
        """繪製初始化按鈕"""
        box = layout.box()
        col = box.column(align=True)
        
        col.label(text="Initialize:", icon='PLAY')
        
        # 檢查是否有 Collection
        collection = scene.warp_collection
        has_collection = collection is not None
        
        # 檢查 Collection 內是否有啟用的物件
        enabled_count = 0
        if has_collection:
            enabled_count = sum(
                1 for obj in collection.all_objects 
                if obj.get("warp_enabled", True)
            )
        
        # 初始化按鈕
        row = col.row()
        row.scale_y = 1.5
        row.enabled = has_collection and enabled_count > 0
        row.operator("warp.initialize", text="Initialize Simulation", icon='PLAY')
        
        # 提示訊息
        if not has_collection:
            col.label(text="⚠ Select a collection", icon='ERROR')
        elif enabled_count == 0:
            col.label(text="⚠ No enabled objects", icon='ERROR')
        else:
            col.label(text=f"✓ {enabled_count} object(s) ready", icon='CHECKMARK')
    
    def _draw_bake_control(self, layout):
        """繪製 Bake 控制按鈕"""
        box = layout.box()
        col = box.column(align=True)
        
        col.label(text="Bake:", icon='REC')
        
        # 檢查是否已初始化
        is_initialized = config.model is not None
        
        # Bake 和 Clear 按鈕
        row = col.row(align=True)
        row.scale_y = 1.5
        row.enabled = is_initialized  # ← 直接在 row 設置
        row.operator("warp.bake_simulation", text="Bake", icon='REC')
        
        # Clear 按鈕（不受限制）
        clear_row = col.row(align=True)
        clear_row.scale_y = 1.5
        clear_row.operator("warp.clear_cache", text="Clear", icon='TRASH')
        
        # Load Cache 按鈕
        col.operator("warp.load_cache", text="Load Existing Cache", icon='FILE_FOLDER')
        
        # 提示訊息
        if not is_initialized:
            col.label(text="⚠ Initialize first", icon='ERROR')
    
    def _draw_cache_status(self, layout):
        """繪製快取狀態資訊"""
        box = layout.box()
        col = box.column(align=True)
        
        col.label(text="Cache Status:", icon='INFO')
        
        # 檢查快取目錄
        if config.cache_dir is None:
            col.label(text="⚠ Cache Dir Not Set", icon='ERROR')
            col.label(text="Please save .blend file", icon='DISK_DRIVE')
            return
        
        # 檢查是否為臨時目錄
        if "temp" in str(config.cache_dir).lower():
            subcol = col.column(align=True)
            subcol.label(text="⚠ Using Temp Dir", icon='ERROR')
            row = subcol.row()
            row.scale_y = 0.8
            row.label(text="Save .blend for permanent cache")
        
        # 快取資訊
        cache_info = config.cache_info
        
        if cache_info['baked']:
            # 已 Bake
            col.label(text="✓ Baked", icon='CHECKMARK')
            
            grid = col.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
            
            # 幀範圍
            grid.label(text="Frames:")
            grid.label(text=f"{cache_info['frame_start']} - {cache_info['frame_end']}")
            
            # 物件數量
            grid.label(text="Objects:")
            grid.label(text=f"{len(cache_info.get('objects', {}))}")
            
            # 總粒子數
            total_particles = sum(
                obj_info.get('particle_count', 0)
                for obj_info in cache_info.get('objects', {}).values()
            )
            grid.label(text="Particles:")
            grid.label(text=f"{total_particles}")
            
            # FPS
            grid.label(text="FPS:")
            grid.label(text=f"{cache_info['fps']}")
            
            # 快取目錄
            if config.cache_dir:
                row = col.row()
                row.scale_y = 0.8
                row.label(text=f"💾 {config.cache_dir.name}", icon='DISK_DRIVE')
        
        else:
            # 未 Bake
            col.label(text="✗ Not Baked", icon='ERROR')
            col.label(text="Initialize and click 'Bake'", icon='HAND')


def register():
    """註冊屬性"""
    Scene = bpy.types.Scene
    
    # === 模擬品質 ===
    Scene.warp_sim_substeps = bpy.props.IntProperty(
        name="Substeps",
        description="Number of simulation substeps per frame (higher = more stable)",
        default=config.DEFAULT_SIM_SUBSTEPS,
        min=1, max=128, soft_max=64
    )
    
    # === 全域接觸參數 ===
    Scene.warp_contact_ke = bpy.props.FloatProperty(
        name="Contact Stiffness",
        default=config.DEFAULT_CONTACT_KE,
        min=1.0e2, max=1.0e5, soft_max=1.0e4,
        precision=0, step=100
    )
    
    Scene.warp_contact_kd = bpy.props.FloatProperty(
        name="Contact Damping",
        default=config.DEFAULT_CONTACT_KD,
        min=0.0, max=1.0, soft_max=0.1,
        precision=6, step=0.01
    )
    
    Scene.warp_contact_kf = bpy.props.FloatProperty(
        name="Friction Stiffness",
        default=config.DEFAULT_CONTACT_KF,
        min=1.0e2, max=1.0e5, soft_max=1.0e4,
        precision=0, step=100
    )
    
    Scene.warp_contact_mu = bpy.props.FloatProperty(
        name="Friction Coefficient",
        default=config.DEFAULT_CONTACT_MU,
        min=0.0, max=2.0, soft_max=1.0,
        precision=2, step=10
    )


def unregister():
    """移除屬性"""
    Scene = bpy.types.Scene
    
    del Scene.warp_sim_substeps
    del Scene.warp_contact_ke
    del Scene.warp_contact_kd
    del Scene.warp_contact_kf
    
    del Scene.warp_contact_mu