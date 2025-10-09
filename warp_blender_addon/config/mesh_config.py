"""
Mesh Config - 網格生成配置
包含 Gmsh 相關參數：Remesh、邊界層、密度分析等
"""

import bpy


# ============================================================
# Gmsh 配置
# ============================================================

# Remesh 設定
DEFAULT_REMESH_MODE = 'NONE'
DEFAULT_REMESH_VOXEL_SIZE = 0.05
DEFAULT_REMESH_OCTREE_DEPTH = 4

# 密度分析
DEFAULT_USE_LOCAL_DENSITY = False  # False = 全域平均，True = 局部密度
DEFAULT_BLUR_RADIUS = 3            # 高斯模糊半徑（1-5）
DEFAULT_OUTLIER_REMOVAL = True     # 去除異常值
DEFAULT_SIZE_CLAMP_RATIO = 3.0     # 尺寸範圍限制倍數

# 邊界層設定
DEFAULT_BL_ENABLED = True          # 啟用邊界層
DEFAULT_BL_THICKNESS = 0.3         # 邊界層厚度
DEFAULT_BL_SIZE_MULTIPLIER = 1.0   # 邊界層尺寸 = 表面平均 × 倍數
DEFAULT_CORE_SIZE_MULTIPLIER = 8.0 # 核心尺寸 = 表面平均 × 倍數

# 算法與優化
DEFAULT_ALGORITHM_3D = 1           # 1=Delaunay, 7=MMG3D
DEFAULT_GMSH_OPTIMIZE = True       # 是否優化網格
DEFAULT_OPTIMIZE_ITERATIONS = 3    # 優化迭代次數
DEFAULT_GMSH_VERBOSE = False       # Gmsh 詳細輸出


# ============================================================
# Gmsh 參數讀取
# ============================================================

def get_remesh_mode():
    """讀取 Remesh 模式"""
    try:
        return bpy.context.scene.warp_remesh_mode
    except:
        return DEFAULT_REMESH_MODE

def get_remesh_voxel_size():
    """讀取 Voxel 大小"""
    try:
        return bpy.context.scene.warp_remesh_voxel_size
    except:
        return DEFAULT_REMESH_VOXEL_SIZE

def get_remesh_octree_depth():
    """讀取 Octree 深度"""
    try:
        return bpy.context.scene.warp_remesh_octree_depth
    except:
        return DEFAULT_REMESH_OCTREE_DEPTH

def get_use_local_density():
    """讀取是否使用局部密度"""
    try:
        return bpy.context.scene.warp_use_local_density
    except:
        return DEFAULT_USE_LOCAL_DENSITY

def get_blur_radius():
    """讀取高斯模糊半徑"""
    try:
        return bpy.context.scene.warp_blur_radius
    except:
        return DEFAULT_BLUR_RADIUS

def get_outlier_removal():
    """讀取是否去除異常值"""
    try:
        return bpy.context.scene.warp_outlier_removal
    except:
        return DEFAULT_OUTLIER_REMOVAL

def get_size_clamp_ratio():
    """讀取尺寸範圍限制倍數"""
    try:
        return bpy.context.scene.warp_size_clamp_ratio
    except:
        return DEFAULT_SIZE_CLAMP_RATIO

def get_bl_enabled():
    """讀取是否啟用邊界層"""
    try:
        return bpy.context.scene.warp_bl_enabled
    except:
        return DEFAULT_BL_ENABLED

def get_bl_thickness():
    """讀取邊界層厚度"""
    try:
        return bpy.context.scene.warp_bl_thickness
    except:
        return DEFAULT_BL_THICKNESS

def get_bl_size_multiplier():
    """讀取邊界層尺寸倍數"""
    try:
        return bpy.context.scene.warp_bl_size_multiplier
    except:
        return DEFAULT_BL_SIZE_MULTIPLIER

def get_core_size_multiplier():
    """讀取核心尺寸倍數"""
    try:
        return bpy.context.scene.warp_core_size_multiplier
    except:
        return DEFAULT_CORE_SIZE_MULTIPLIER

def get_algorithm_3d():
    """讀取 3D 算法（返回整數）"""
    try:
        # EnumProperty 返回字串，需轉換為整數
        return int(bpy.context.scene.warp_algorithm_3d)
    except:
        return DEFAULT_ALGORITHM_3D

def get_gmsh_optimize():
    """讀取是否優化網格"""
    try:
        return bpy.context.scene.warp_gmsh_optimize
    except:
        return DEFAULT_GMSH_OPTIMIZE

def get_optimize_iterations():
    """讀取優化迭代次數"""
    try:
        return bpy.context.scene.warp_optimize_iterations
    except:
        return DEFAULT_OPTIMIZE_ITERATIONS

def get_gmsh_verbose():
    """讀取是否顯示詳細輸出"""
    try:
        return bpy.context.scene.warp_gmsh_verbose
    except:
        return DEFAULT_GMSH_VERBOSE