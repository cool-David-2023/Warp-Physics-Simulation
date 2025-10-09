"""
Generate Panel - 四面體生成面板
支援 Gmsh 和 Grid 兩種模式切換
"""

import bpy
from .. import config


class WARP_PT_GeneratePanel(bpy.types.Panel):
    """Generate Tetrahedra 面板"""
    
    bl_label = "Generate Tetrahedra"
    bl_idname = "WARP_PT_generate_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Warp'
    bl_order = 1
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 模式切換按鈕
        self._draw_mode_switch(layout, scene)
        
        layout.separator()
        
        # 根據模式顯示對應參數
        if scene.warp_generate_mode == 'GMSH':
            self._draw_gmsh_settings(layout, scene)
        else:  # GRID
            self._draw_grid_settings(layout, scene)
    
    def _draw_mode_switch(self, layout, scene):
        """繪製模式切換按鈕"""
        row = layout.row(align=True)
        row.prop(scene, "warp_generate_mode", expand=True)
    
    def _draw_gmsh_settings(self, layout, scene):
        """繪製 Gmsh 設定區域"""
        box = layout.box()
        col = box.column(align=True)
        
        # === Remesh 設定 ===
        col.label(text="Remesh (Optional):", icon='MOD_REMESH')
        col.prop(scene, "warp_remesh_mode", text="Mode")
        
        if scene.warp_remesh_mode == 'VOXEL':
            col.prop(scene, "warp_remesh_voxel_size", text="Voxel Size")
        elif scene.warp_remesh_mode in ['SMOOTH', 'SHARP']:
            col.prop(scene, "warp_remesh_octree_depth", text="Octree Depth")
        
        col.separator()
        
        # === 密度分析 ===
        col.label(text="Density Analysis:", icon='MESH_DATA')
        col.prop(scene, "warp_use_local_density", text="Use Local Density")
        
        if scene.warp_use_local_density:
            subcol = col.column(align=True)
            subcol.enabled = scene.warp_use_local_density
            subcol.prop(scene, "warp_blur_radius", text="Blur Radius")
            subcol.prop(scene, "warp_outlier_removal", text="Remove Outliers")
            subcol.prop(scene, "warp_size_clamp_ratio", text="Size Clamp Ratio")
        
        col.separator()
        
        # === 邊界層 ===
        col.label(text="Boundary Layer:", icon='MOD_SOLIDIFY')
        col.prop(scene, "warp_bl_enabled", text="Enable Boundary Layer")
        
        if scene.warp_bl_enabled:
            subcol = col.column(align=True)
            subcol.enabled = scene.warp_bl_enabled
            subcol.prop(scene, "warp_bl_thickness", text="Thickness")
            subcol.prop(scene, "warp_bl_size_multiplier", text="BL Size Multiplier")
            subcol.prop(scene, "warp_core_size_multiplier", text="Core Size Multiplier")
        
        col.separator()
        
        # === 算法與優化 ===
        col.label(text="Algorithm & Optimization:", icon='SETTINGS')
        subcol = col.column(align=True)
        subcol.prop(scene, "warp_algorithm_3d", text="Algorithm")
        subcol.prop(scene, "warp_gmsh_optimize", text="Optimize Mesh")
        
        if scene.warp_gmsh_optimize:
            subcol.prop(scene, "warp_optimize_iterations", text="Iterations")
        
        subcol.prop(scene, "warp_gmsh_verbose", text="Verbose Output")
        
        col.separator()
        
        # === Generate 按鈕 ===
        col.scale_y = 1.5
        op = col.operator("warp.generate_gmsh", text="Generate Tetrahedra (Gmsh)", icon='MESH_ICOSPHERE')
        
        # 狀態顯示
        if hasattr(config, 'object_tet_data') and len(config.object_tet_data) > 0:
            row = box.row()
            row.alignment = 'CENTER'
            total_tets = sum(
                data.get('stats', {}).get('tet_count', 0) 
                for data in config.object_tet_data.values()
            )
            row.label(text=f"✓ {total_tets:,} total tets", icon='CHECKMARK')
    
    def _draw_grid_settings(self, layout, scene):
        """繪製 Grid 設定區域"""
        box = layout.box()
        col = box.column(align=True)
        
        # === Grid 參數 ===
        col.label(text="Grid Settings:", icon='MESH_GRID')
        subcol = col.column(align=True)
        subcol.prop(scene, "warp_cell_dim", text="Grid Dimension")
        subcol.prop(scene, "warp_cell_size", text="Cell Size (m)")
        subcol.prop(scene, "warp_start_height", text="Start Height (m)")
        
        # 粒子數估算
        particle_estimate = (scene.warp_cell_dim + 1) ** 3
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text=f"≈ {particle_estimate} particles", icon='INFO')
        
        col.separator()
        
        # === Generate 按鈕 ===
        col.scale_y = 1.5
        col.operator("warp.generate_grid", text="Generate Tetrahedra (Grid)", icon='MESH_CUBE')


def register():
    """註冊屬性"""
    Scene = bpy.types.Scene
    
    # === 模式切換 ===
    Scene.warp_generate_mode = bpy.props.EnumProperty(
        name="Generate Mode",
        items=[
            ('GMSH', 'Gmsh Settings', 'Generate tetrahedra using Gmsh'),
            ('GRID', 'Grid Settings', 'Generate regular grid'),
        ],
        default='GMSH'
    )
    
    # === Grid 設定 ===
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
        default=config.DEFAULT_USE_LOCAL_DENSITY
    )
    
    Scene.warp_blur_radius = bpy.props.IntProperty(
        name="Blur Radius",
        default=config.DEFAULT_BLUR_RADIUS,
        min=1, max=10, soft_max=5
    )
    
    Scene.warp_outlier_removal = bpy.props.BoolProperty(
        name="Remove Outliers",
        default=config.DEFAULT_OUTLIER_REMOVAL
    )
    
    Scene.warp_size_clamp_ratio = bpy.props.FloatProperty(
        name="Size Clamp Ratio",
        default=config.DEFAULT_SIZE_CLAMP_RATIO,
        min=1.0, max=10.0, soft_max=5.0,
        precision=1
    )
    
    # === 邊界層 ===
    Scene.warp_bl_enabled = bpy.props.BoolProperty(
        name="Enable Boundary Layer",
        default=config.DEFAULT_BL_ENABLED
    )
    
    Scene.warp_bl_thickness = bpy.props.FloatProperty(
        name="BL Thickness",
        default=config.DEFAULT_BL_THICKNESS,
        min=0.01, max=2.0, soft_max=1.0,
        precision=2
    )
    
    Scene.warp_bl_size_multiplier = bpy.props.FloatProperty(
        name="BL Size Multiplier",
        default=config.DEFAULT_BL_SIZE_MULTIPLIER,
        min=0.1, max=5.0, soft_max=2.0,
        precision=1
    )
    
    Scene.warp_core_size_multiplier = bpy.props.FloatProperty(
        name="Core Size Multiplier",
        default=config.DEFAULT_CORE_SIZE_MULTIPLIER,
        min=1.0, max=20.0, soft_max=10.0,
        precision=1
    )
    
    # === 算法與優化 ===
    Scene.warp_algorithm_3d = bpy.props.EnumProperty(
        name="3D Algorithm",
        items=[
            ('1', 'Delaunay', 'Delaunay algorithm'),
            ('7', 'MMG3D', 'MMG3D algorithm'),
        ],
        default='1'
    )
    
    Scene.warp_gmsh_optimize = bpy.props.BoolProperty(
        name="Optimize Mesh",
        default=config.DEFAULT_GMSH_OPTIMIZE
    )
    
    Scene.warp_optimize_iterations = bpy.props.IntProperty(
        name="Optimize Iterations",
        default=config.DEFAULT_OPTIMIZE_ITERATIONS,
        min=1, max=10, soft_max=5
    )
    
    Scene.warp_gmsh_verbose = bpy.props.BoolProperty(
        name="Verbose Output",
        default=config.DEFAULT_GMSH_VERBOSE
    )


def unregister():
    """移除屬性"""
    Scene = bpy.types.Scene
    
    # 模式切換
    del Scene.warp_generate_mode
    
    # Grid 設定
    del Scene.warp_cell_dim
    del Scene.warp_cell_size
    del Scene.warp_start_height
    
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