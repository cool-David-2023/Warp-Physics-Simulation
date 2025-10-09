"""
Config 模組 - 集中管理所有配置
重構：拆分為 simulation_config, mesh_config, utils
"""

# 導入所有子模組
from .simulation_config import *
from .mesh_config import *
from .utils import *

__all__ = [
    # === Simulation Config ===
    # Presets
    'PRESETS',
    
    # 預設模擬參數
    'DEFAULT_CELL_DIM',
    'DEFAULT_CELL_SIZE',
    'DEFAULT_START_HEIGHT',
    'DEFAULT_DENSITY',
    'DEFAULT_K_MU',
    'DEFAULT_K_LAMBDA',
    'DEFAULT_K_DAMP',
    'DEFAULT_SIM_SUBSTEPS',
    'DEFAULT_CONTACT_KE',
    'DEFAULT_CONTACT_KD',
    'DEFAULT_CONTACT_KF',
    'DEFAULT_CONTACT_MU',
    
    # 模擬參數 Getters
    'get_cell_dim',
    'get_cell_size',
    'get_start_height',
    'get_sim_substeps',
    
    # === Mesh Config ===
    # Gmsh 預設參數
    'DEFAULT_REMESH_MODE',
    'DEFAULT_REMESH_VOXEL_SIZE',
    'DEFAULT_REMESH_OCTREE_DEPTH',
    'DEFAULT_USE_LOCAL_DENSITY',
    'DEFAULT_BLUR_RADIUS',
    'DEFAULT_OUTLIER_REMOVAL',
    'DEFAULT_SIZE_CLAMP_RATIO',
    'DEFAULT_BL_ENABLED',
    'DEFAULT_BL_THICKNESS',
    'DEFAULT_BL_SIZE_MULTIPLIER',
    'DEFAULT_CORE_SIZE_MULTIPLIER',
    'DEFAULT_ALGORITHM_3D',
    'DEFAULT_GMSH_OPTIMIZE',
    'DEFAULT_OPTIMIZE_ITERATIONS',
    'DEFAULT_GMSH_VERBOSE',
    
    # Gmsh 參數 Getters
    'get_remesh_mode',
    'get_remesh_voxel_size',
    'get_remesh_octree_depth',
    'get_use_local_density',
    'get_blur_radius',
    'get_outlier_removal',
    'get_size_clamp_ratio',
    'get_bl_enabled',
    'get_bl_thickness',
    'get_bl_size_multiplier',
    'get_core_size_multiplier',
    'get_algorithm_3d',
    'get_gmsh_optimize',
    'get_optimize_iterations',
    'get_gmsh_verbose',
    
    # === Utils ===
    # 快取設定
    'CACHE_DIR_NAME',
    
    # 全域變數
    'model',
    'state_0',
    'state_1',
    'integrator',
    'wireframe_objects',
    'cache_dir',
    'cache_info',
    'object_tet_data',
    
    # 輔助函數
    'get_cache_directory',
    'initialize_cache_directory',
    'reset_global_state',
    'get_simulation_info',
    'print_config',
    'get_object_material',
    'set_object_material',
    
    # 插件資訊
    'ADDON_VERSION',
    'ADDON_NAME',
    'ADDON_AUTHOR',
    'ADDON_DESCRIPTION',
]