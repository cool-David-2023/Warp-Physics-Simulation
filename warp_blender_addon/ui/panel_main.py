"""
Warp 模擬控制介面 - 五個獨立面板
支援 Gmsh 進階功能與 Material Library 彈出式設計
"""

import bpy
from .. import config


# ========== Material Library 彈出式操作者 ==========

class WARP_OT_OpenMaterialLibrary(bpy.types.Operator):
    """開啟材質庫彈出視窗"""
    bl_idname = "warp.open_material_library"
    bl_label = "Material Library"
    bl_description = "Open material library"

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        
        # 標題
        row = layout.row(align=True)
        row.label(text="Material Library", icon='MATERIAL')
        
        layout.separator()
        
        # 材質預設列表
        col = layout.column(align=True)
        for preset_key in sorted(config.PRESETS.keys()):
            preset_data = config.PRESETS[preset_key]
            preset_name = preset_data['name'].split('(')[0].strip()
            
            row = col.row(align=True)
            # 應用按鈕（無邊框）
            op = row.operator(
                "warp.apply_preset", 
                text=preset_name, 
                emboss=False
            )
            op.preset = preset_key
            
            # 刪除按鈕（可選，如果支援自訂材質）
            # row.operator("warp.delete_preset", text="", icon='X', emboss=False)
        
        # 新增自訂材質區域（未來功能）
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, "warp_new_preset_name", text="", placeholder="New Material...")
        row.operator("warp.save_preset", text="", icon='ADD', emboss=False)
    
    def execute(self, context):
        return {'FINISHED'}


class WARP_OT_ApplyPreset(bpy.types.Operator):
    """應用材質預設"""
    bl_idname = "warp.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply material preset to properties"
    
    preset: bpy.props.StringProperty()

    def execute(self, context):
        if self.preset not in config.PRESETS:
            self.report({'ERROR'}, f"Preset '{self.preset}' not found")
            return {'CANCELLED'}
        
        preset = config.PRESETS[self.preset]
        scene = context.scene
        
        # 應用材質參數
        scene.warp_density = preset['density']
        scene.warp_k_mu = preset['k_mu']
        scene.warp_k_lambda = preset['k_lambda']
        scene.warp_k_damp = preset['k_damp']
        
        preset_name = preset['name'].split('(')[0].strip()
        self.report({'INFO'}, f"Applied preset: {preset_name}")
        return {'FINISHED'}


class WARP_OT_SavePreset(bpy.types.Operator):
    """儲存自訂材質預設"""
    bl_idname = "warp.save_preset"
    bl_label = "Save Preset"
    bl_description = "Save current settings as a new preset"

    def execute(self, context):
        preset_name = context.scene.warp_new_preset_name.strip()
        
        if not preset_name:
            self.report({'WARNING'}, "Preset name cannot be empty")
            return {'CANCELLED'}
        
        # TODO: 實作自訂材質儲存功能
        self.report({'INFO'}, f"Custom presets not yet implemented")
        return {'FINISHED'}


class WARP_OT_ResetParameters(bpy.types.Operator):
    """重置參數為預設值"""
    bl_idname = "warp.reset_parameters"
    bl_label = "Reset to Defaults"
    bl_description = "Reset all parameters to default values"
    
    def execute(self, context):
        scene = context.scene
        
        # 重置所有參數
        scene.warp_density = config.DEFAULT_DENSITY
        scene.warp_k_mu = config.DEFAULT_K_MU
        scene.warp_k_lambda = config.DEFAULT_K_LAMBDA
        scene.warp_k_damp = config.DEFAULT_K_DAMP
        scene.warp_sim_substeps = config.DEFAULT_SIM_SUBSTEPS
        scene.warp_contact_ke = config.DEFAULT_CONTACT_KE
        scene.warp_contact_kd = config.DEFAULT_CONTACT_KD
        scene.warp_contact_kf = config.DEFAULT_CONTACT_KF
        scene.warp_contact_mu = config.DEFAULT_CONTACT_MU
        
        self.report({'INFO'}, "Reset to default values")
        return {'FINISHED'}


# ========== Panel 1: Simulation Parameters ==========

class WARP_PT_SimulationPanel(bpy.types.Panel):
    """模擬參數面板"""
    
    bl_label = "Simulation Parameters"
    bl_idname = "WARP_PT_simulation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 1
    
    def draw_header_preset(self, context):
        """在標題列繪製 Preset 按鈕"""
        layout = self.layout
        layout.operator(
            "warp.open_material_library",
            text="",
            icon='MATERIAL',
            emboss=False
        )
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Material Properties
        box = layout.box()
        box.label(text="Material Properties", icon='PHYSICS')
        
        col = box.column(align=True)
        col.prop(scene, "warp_density", text="Density (kg/m³)")
        col.prop(scene, "warp_k_mu", text="Shear Modulus")
        col.prop(scene, "warp_k_lambda", text="Bulk Modulus")
        col.prop(scene, "warp_k_damp", text="Damping")
        
        layout.separator()
        
        # Contact Settings
        box = layout.box()
        box.label(text="Contact Settings", icon='HAND')
        
        col = box.column(align=True)
        col.prop(scene, "warp_contact_ke", text="Contact Stiffness")
        col.prop(scene, "warp_contact_kd", text="Contact Damping")
        col.prop(scene, "warp_contact_kf", text="Friction Stiffness")
        col.prop(scene, "warp_contact_mu", text="Friction Coefficient")
        
        layout.separator()
        
        # Simulation Quality
        box = layout.box()
        box.label(text="Simulation Quality", icon='SETTINGS')
        
        col = box.column(align=True)
        col.prop(scene, "warp_sim_substeps", text="Substeps per Frame")
        
        fps = scene.render.fps
        substeps = scene.warp_sim_substeps
        dt = 1.0 / (fps * substeps)
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text=f"dt ≈ {dt:.6f}s", icon='TIME')
        
        layout.separator()
        
        # Reset Button
        layout.operator("warp.reset_parameters", text="Reset to Defaults", icon='LOOP_BACK')


# ========== Panel 2: Gmsh Settings ==========

class WARP_PT_GmshPanel(bpy.types.Panel):
    """Gmsh 設定面板"""
    
    bl_label = "Gmsh Settings"
    bl_idname = "WARP_PT_gmsh_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 2
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Remesh Settings
        box = layout.box()
        box.label(text="Remesh (Optional)", icon='MOD_REMESH')
        
        col = box.column(align=True)
        col.prop(scene, "warp_remesh_mode", text="Mode")
        
        if scene.warp_remesh_mode == 'VOXEL':
            col.prop(scene, "warp_remesh_voxel_size", text="Voxel Size")
        elif scene.warp_remesh_mode in ['SMOOTH', 'SHARP']:
            col.prop(scene, "warp_remesh_octree_depth", text="Octree Depth")
        
        layout.separator()
        
        # Density Analysis
        box = layout.box()
        box.label(text="Density Analysis", icon='MESH_DATA')
        
        col = box.column(align=True)
        col.prop(scene, "warp_use_local_density", text="Use Local Density")
        
        if scene.warp_use_local_density:
            subcol = col.column(align=True)
            subcol.enabled = scene.warp_use_local_density
            subcol.prop(scene, "warp_blur_radius", text="Blur Radius")
            subcol.prop(scene, "warp_outlier_removal", text="Remove Outliers")
            subcol.prop(scene, "warp_size_clamp_ratio", text="Size Clamp Ratio")
        
        layout.separator()
        
        # Boundary Layer
        box = layout.box()
        box.label(text="Boundary Layer", icon='MOD_SOLIDIFY')
        
        col = box.column(align=True)
        col.prop(scene, "warp_bl_enabled", text="Enable Boundary Layer")
        
        if scene.warp_bl_enabled:
            subcol = col.column(align=True)
            subcol.enabled = scene.warp_bl_enabled
            subcol.prop(scene, "warp_bl_thickness", text="Thickness")
            subcol.prop(scene, "warp_bl_size_multiplier", text="BL Size Multiplier")
            subcol.prop(scene, "warp_core_size_multiplier", text="Core Size Multiplier")
        
        layout.separator()
        
        # Algorithm & Optimization
        box = layout.box()
        box.label(text="Algorithm & Optimization", icon='SETTINGS')
        
        col = box.column(align=True)
        col.prop(scene, "warp_algorithm_3d", text="Algorithm")
        col.prop(scene, "warp_gmsh_optimize", text="Optimize Mesh")
        
        if scene.warp_gmsh_optimize:
            col.prop(scene, "warp_optimize_iterations", text="Iterations")
        
        col.prop(scene, "warp_gmsh_verbose", text="Verbose Output")
        
        layout.separator()
        
        # Generate Button
        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("warp.generate_gmsh", text="Generate Tetrahedra (Gmsh)", icon='MESH_ICOSPHERE')
        
        # Status Display
        if hasattr(config, 'tet_data') and config.tet_data is not None:
            stats = config.tet_data.get('stats', {})
            tet_count = stats.get('tet_count', len(config.tet_data['elements']))
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text=f"✓ {tet_count:,} tets", icon='CHECKMARK')


# ========== Panel 3: Grid Settings ==========

class WARP_PT_GridPanel(bpy.types.Panel):
    """網格設定面板"""
    
    bl_label = "Grid Settings"
    bl_idname = "WARP_PT_grid_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 3
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.label(text="Grid Configuration", icon='MESH_GRID')
        
        col = box.column(align=True)
        col.prop(scene, "warp_cell_dim", text="Grid Dimension")
        col.prop(scene, "warp_cell_size", text="Cell Size (m)")
        col.prop(scene, "warp_start_height", text="Start Height (m)")
        
        particle_estimate = (scene.warp_cell_dim + 1) ** 3
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text=f"≈ {particle_estimate:,} particles", icon='INFO')


# ========== Panel 4: Bake Control ==========

class WARP_PT_BakePanel(bpy.types.Panel):
    """烘焙控制面板"""
    
    bl_label = "Bake Control"
    bl_idname = "WARP_PT_bake_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 4
    
    def draw(self, context):
        layout = self.layout
        
        # Initialize Section
        box = layout.box()
        box.label(text="Initialize", icon='MESH_GRID')
        
        col = box.column(align=True)
        col.scale_y = 1.2
        col.operator("warp.init_model", text="Init Grid", icon='MESH_CUBE')
        
        has_tet = hasattr(config, 'tet_data') and config.tet_data is not None
        row = col.row()
        row.scale_y = 1.2
        row.enabled = has_tet
        row.operator("warp.init_from_tet", text="Init from Gmsh", icon='MESH_ICOSPHERE')
        
        layout.separator()
        
        # Bake Section
        box = layout.box()
        box.label(text="Simulation Bake", icon='REC')
        
        col = box.column(align=True)
        
        row = col.row(align=True)
        row.scale_y = 1.5
        row.operator("warp.bake_simulation", text="Bake", icon='REC')
        row.operator("warp.clear_cache", text="Clear", icon='TRASH')
        
        col.operator("warp.load_cache", text="Load Existing Cache", icon='FILE_FOLDER')


# ========== Panel 5: Status ==========

class WARP_PT_StatusPanel(bpy.types.Panel):
    """狀態顯示面板"""
    
    bl_label = "Status"
    bl_idname = "WARP_PT_status_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 5
    
    def draw(self, context):
        layout = self.layout
        
        # Cache Directory Warning
        if config.cache_dir is None:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="⚠ Cache Dir Not Set", icon='ERROR')
            col.label(text="Please save .blend file", icon='DISK_DRIVE')
            return
        
        if "temp" in str(config.cache_dir).lower():
            box = layout.box()
            col = box.column(align=True)
            col.label(text="⚠ Using Temp Dir", icon='ERROR')
            row = col.row()
            row.scale_y = 0.8
            row.label(text="Save .blend for permanent cache")
        
        # Cache Status
        cache_info = config.cache_info
        
        box = layout.box()
        
        if cache_info['baked']:
            col = box.column(align=True)
            col.label(text="✓ Baked", icon='CHECKMARK')
            
            col.separator()
            
            grid = col.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
            
            grid.label(text="Frames:")
            grid.label(text=f"{cache_info['frame_start']} - {cache_info['frame_end']}")
            
            grid.label(text="Particles:")
            grid.label(text=f"{cache_info['particle_count']:,}")
            
            grid.label(text="FPS:")
            grid.label(text=f"{cache_info['fps']}")
            
            if config.cache_dir:
                col.separator()
                row = col.row()
                row.scale_y = 0.8
                row.alignment = 'CENTER'
                row.label(text=f"💾 {config.cache_dir.name}", icon='DISK_DRIVE')
        else:
            col = box.column(align=True)
            col.label(text="✗ Not Baked", icon='ERROR')
            col.label(text="Set parameters and click 'Bake'", icon='HAND')


# ========== 註冊 ==========

def register():
    """註冊自定義屬性"""
    Scene = bpy.types.Scene
    
    # === 網格設定 ===
    Scene.warp_cell_dim = bpy.props.IntProperty(
        name="Grid Dimension",
        default=config.DEFAULT_CELL_DIM,
        min=2, max=20, soft_max=10
    )
    
    Scene.warp_cell_size = bpy.props.FloatProperty(
        name="Cell Size",
        default=config.DEFAULT_CELL_SIZE,
        min=0.1, max=2.0, soft_max=1.0,
        precision=2, step=10
    )
    
    Scene.warp_start_height = bpy.props.FloatProperty(
        name="Start Height",
        default=config.DEFAULT_START_HEIGHT,
        min=0.5, max=10.0, soft_max=5.0,
        precision=2, step=10
    )
    
    # === 材質參數 ===
    Scene.warp_density = bpy.props.FloatProperty(
        name="Density",
        default=config.DEFAULT_DENSITY,
        min=10.0, max=1000.0, soft_max=500.0,
        precision=1, step=100
    )
    
    Scene.warp_k_mu = bpy.props.FloatProperty(
        name="Shear Modulus",
        default=config.DEFAULT_K_MU,
        min=100.0, max=50000.0, soft_max=20000.0,
        precision=0, step=10000
    )
    
    Scene.warp_k_lambda = bpy.props.FloatProperty(
        name="Bulk Modulus",
        default=config.DEFAULT_K_LAMBDA,
        min=500.0, max=100000.0, soft_max=50000.0,
        precision=0, step=10000
    )
    
    Scene.warp_k_damp = bpy.props.FloatProperty(
        name="Damping",
        default=config.DEFAULT_K_DAMP,
        min=0.0, max=5.0, soft_max=2.0,
        precision=2, step=1
    )
    
    # === 模擬品質 ===
    Scene.warp_sim_substeps = bpy.props.IntProperty(
        name="Substeps",
        default=config.DEFAULT_SIM_SUBSTEPS,
        min=1, max=128, soft_max=64
    )
    
    # === 接觸參數 ===
    Scene.warp_contact_ke = bpy.props.FloatProperty(
        name="Contact Stiffness",
        description="Contact stiffness (lower = softer contact)",
        default=config.DEFAULT_CONTACT_KE,
        min=1.0e2, max=1.0e5, soft_max=1.0e4,
        precision=0, step=100,
        subtype='FACTOR'
    )
    
    Scene.warp_contact_kd = bpy.props.FloatProperty(
        name="Contact Damping",
        description="Contact damping (usually 0.0)",
        default=config.DEFAULT_CONTACT_KD,
        min=0.0, max=1.0, soft_max=0.1,
        precision=6, step=0.01
    )
    
    Scene.warp_contact_kf = bpy.props.FloatProperty(
        name="Friction Stiffness",
        description="Friction force stiffness",
        default=config.DEFAULT_CONTACT_KF,
        min=1.0e2, max=1.0e5, soft_max=1.0e4,
        precision=0, step=100,
        subtype='FACTOR'
    )
    
    Scene.warp_contact_mu = bpy.props.FloatProperty(
        name="Friction Coefficient",
        description="Friction coefficient (0.0 = frictionless)",
        default=config.DEFAULT_CONTACT_MU,
        min=0.0, max=2.0, soft_max=1.0,
        precision=2, step=10
    )
    
    # === Gmsh Remesh 設定 ===
    Scene.warp_remesh_mode = bpy.props.EnumProperty(
        name="Remesh Mode",
        items=[
            ('NONE', 'None', 'No remeshing'),
            ('VOXEL', 'Voxel', 'Voxel-based remeshing'),
            ('SMOOTH', 'Smooth', 'Smooth remeshing'),
            ('SHARP', 'Sharp', 'Sharp feature preservation'),
        ],
        default='NONE'
    )
    
    Scene.warp_remesh_voxel_size = bpy.props.FloatProperty(
        name="Voxel Size",
        default=config.DEFAULT_REMESH_VOXEL_SIZE,
        min=0.01, max=1.0,
        precision=3
    )
    
    Scene.warp_remesh_octree_depth = bpy.props.IntProperty(
        name="Octree Depth",
        default=config.DEFAULT_REMESH_OCTREE_DEPTH,
        min=1, max=8
    )
    
    # === 密度分析 ===
    Scene.warp_use_local_density = bpy.props.BoolProperty(
        name="Use Local Density",
        description="Use local density analysis (requires SciPy)",
        default=config.DEFAULT_USE_LOCAL_DENSITY
    )
    
    Scene.warp_blur_radius = bpy.props.IntProperty(
        name="Blur Radius",
        description="Gaussian blur radius for smoothing",
        default=config.DEFAULT_BLUR_RADIUS,
        min=1, max=10, soft_max=5
    )
    
    Scene.warp_outlier_removal = bpy.props.BoolProperty(
        name="Remove Outliers",
        description="Remove statistical outliers from density analysis",
        default=config.DEFAULT_OUTLIER_REMOVAL
    )
    
    Scene.warp_size_clamp_ratio = bpy.props.FloatProperty(
        name="Size Clamp Ratio",
        description="Limit size variation range",
        default=config.DEFAULT_SIZE_CLAMP_RATIO,
        min=1.0, max=10.0, soft_max=5.0,
        precision=1
    )
    
    # === 邊界層 ===
    Scene.warp_bl_enabled = bpy.props.BoolProperty(
        name="Enable Boundary Layer",
        description="Use boundary layer mesh refinement",
        default=config.DEFAULT_BL_ENABLED
    )
    
    Scene.warp_bl_thickness = bpy.props.FloatProperty(
        name="BL Thickness",
        description="Boundary layer thickness",
        default=config.DEFAULT_BL_THICKNESS,
        min=0.01, max=2.0, soft_max=1.0,
        precision=2
    )
    
    Scene.warp_bl_size_multiplier = bpy.props.FloatProperty(
        name="BL Size Multiplier",
        description="Boundary layer size = surface avg × multiplier",
        default=config.DEFAULT_BL_SIZE_MULTIPLIER,
        min=0.1, max=5.0, soft_max=2.0,
        precision=1
    )
    
    Scene.warp_core_size_multiplier = bpy.props.FloatProperty(
        name="Core Size Multiplier",
        description="Core size = surface avg × multiplier",
        default=config.DEFAULT_CORE_SIZE_MULTIPLIER,
        min=1.0, max=20.0, soft_max=10.0,
        precision=1
    )
    
    # === 算法與優化 ===
    Scene.warp_algorithm_3d = bpy.props.EnumProperty(
        name="3D Algorithm",
        items=[
            ('1', 'Delaunay', 'Delaunay algorithm (default)'),
            ('7', 'MMG3D', 'MMG3D algorithm'),
        ],
        default='1'
    )
    
    Scene.warp_gmsh_optimize = bpy.props.BoolProperty(
        name="Optimize Mesh",
        description="Optimize mesh quality using Netgen",
        default=config.DEFAULT_GMSH_OPTIMIZE
    )
    
    Scene.warp_optimize_iterations = bpy.props.IntProperty(
        name="Optimize Iterations",
        description="Number of optimization iterations",
        default=config.DEFAULT_OPTIMIZE_ITERATIONS,
        min=1, max=10, soft_max=5
    )
    
    Scene.warp_gmsh_verbose = bpy.props.BoolProperty(
        name="Verbose Output",
        description="Show detailed Gmsh output in console",
        default=config.DEFAULT_GMSH_VERBOSE
    )
    
    # === Material Library ===
    Scene.warp_new_preset_name = bpy.props.StringProperty(
        name="New Preset",
        description="Name for the new preset",
        default=""
    )


def unregister():
    """移除自定義屬性"""
    Scene = bpy.types.Scene
    
    # 網格設定
    del Scene.warp_cell_dim
    del Scene.warp_cell_size
    del Scene.warp_start_height
    
    # 材質參數
    del Scene.warp_density
    del Scene.warp_k_mu
    del Scene.warp_k_lambda
    del Scene.warp_k_damp
    
    # 模擬品質
    del Scene.warp_sim_substeps
    
    # 接觸參數
    del Scene.warp_contact_ke
    del Scene.warp_contact_kd
    del Scene.warp_contact_kf
    del Scene.warp_contact_mu
    
    # Gmsh 設定
    del Scene.warp_remesh_mode
    del Scene.warp_remesh_voxel_size
    del Scene.warp_remesh_octree_depth
    del Scene.warp_use_local_density
    del Scene.warp_blur_radius
    del Scene.warp_outlier_removal
    del Scene.warp_size_clamp_ratio
    del Scene.warp_bl_enabled
    del Scene.warp_bl_thickness
    del Scene.warp_bl_size_multiplier
    del Scene.warp_core_size_multiplier
    del Scene.warp_algorithm_3d
    del Scene.warp_gmsh_optimize
    del Scene.warp_optimize_iterations
    del Scene.warp_gmsh_verbose
    
    # Material Library
    del Scene.warp_new_preset_name