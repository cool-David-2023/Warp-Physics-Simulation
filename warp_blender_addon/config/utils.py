"""
Config Utils - 全域變數與輔助函數
包含快取設定、狀態管理、輔助函數等
"""

import bpy
from pathlib import Path
import tempfile


# ============================================================
# 快取設定
# ============================================================

CACHE_DIR_NAME = "warp_cache"


# ============================================================
# 全域變數（模擬狀態）
# ============================================================

# Warp 模擬核心
model = None
state_0 = None
state_1 = None
integrator = None

# Blender 物件
wireframe_objects = {}  # {obj_name: wireframe_obj}

# 快取
cache_dir = None
cache_info = {
    'frame_start': 1,
    'frame_end': 250,
    'fps': 24,
    'baked': False,
    'objects': {}  # {obj_name: {'particle_count': N, 'particle_offset': M}}
}

# 物件四面體數據（{obj_name: {'vertices': array, 'elements': array, 'stats': dict}}）
object_tet_data = {}


# ============================================================
# 快取目錄管理
# ============================================================

def get_cache_directory():
    """獲取快取目錄路徑"""
    blend_filepath = bpy.data.filepath
    
    if not blend_filepath:
        temp_dir = Path(tempfile.gettempdir()) / "warp_cache_temp"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir
    
    blend_dir = Path(blend_filepath).parent
    cache_dir_path = blend_dir / CACHE_DIR_NAME
    cache_dir_path.mkdir(exist_ok=True)
    
    return cache_dir_path

def initialize_cache_directory():
    """初始化快取目錄"""
    global cache_dir
    cache_dir = get_cache_directory()


# ============================================================
# 狀態管理
# ============================================================

def reset_global_state():
    """重置全域狀態"""
    global model, state_0, state_1, integrator, wireframe_objects, object_tet_data
    
    model = None
    state_0 = None
    state_1 = None
    integrator = None
    wireframe_objects = {}
    object_tet_data = {}
    
    cache_info['baked'] = False
    cache_info['objects'] = {}

def get_simulation_info():
    """獲取模擬資訊"""
    return {
        'model_initialized': model is not None,
        'particle_count': model.particle_count if model else 0,
        'cache_baked': cache_info['baked'],
        'cache_dir': str(cache_dir) if cache_dir else None,
        'wireframe_count': len(wireframe_objects),
        'tet_data_count': len(object_tet_data),
    }


# ============================================================
# 物件材質輔助函數
# ============================================================

def get_object_material(obj):
    """獲取物件的完整材質參數字典"""
    from .simulation_config import (
        get_object_density, get_object_k_mu, get_object_k_lambda, get_object_k_damp,
        get_object_contact_ke, get_object_contact_kd, get_object_contact_kf, get_object_contact_mu
    )
    
    return {
        'density': get_object_density(obj),
        'k_mu': get_object_k_mu(obj),
        'k_lambda': get_object_k_lambda(obj),
        'k_damp': get_object_k_damp(obj),
        'contact_ke': get_object_contact_ke(obj),
        'contact_kd': get_object_contact_kd(obj),
        'contact_kf': get_object_contact_kf(obj),
        'contact_mu': get_object_contact_mu(obj),
    }

def set_object_material(obj, material_dict):
    """設置物件的完整材質參數"""
    from .simulation_config import (
        set_object_density, set_object_k_mu, set_object_k_lambda, set_object_k_damp,
        set_object_contact_ke, set_object_contact_kd, set_object_contact_kf, set_object_contact_mu
    )
    
    if 'density' in material_dict:
        set_object_density(obj, material_dict['density'])
    if 'k_mu' in material_dict:
        set_object_k_mu(obj, material_dict['k_mu'])
    if 'k_lambda' in material_dict:
        set_object_k_lambda(obj, material_dict['k_lambda'])
    if 'k_damp' in material_dict:
        set_object_k_damp(obj, material_dict['k_damp'])
    if 'contact_ke' in material_dict:
        set_object_contact_ke(obj, material_dict['contact_ke'])
    if 'contact_kd' in material_dict:
        set_object_contact_kd(obj, material_dict['contact_kd'])
    if 'contact_kf' in material_dict:
        set_object_contact_kf(obj, material_dict['contact_kf'])
    if 'contact_mu' in material_dict:
        set_object_contact_mu(obj, material_dict['contact_mu'])


# ============================================================
# 配置資訊顯示
# ============================================================

def print_config():
    """列印當前配置"""
    from .simulation_config import get_cell_dim, get_cell_size, get_start_height, get_sim_substeps
    from .mesh_config import get_remesh_mode, get_use_local_density, get_bl_enabled, get_gmsh_optimize
    
    print("\n" + "=" * 60)
    print("⚙️ Warp Simulation Configuration")
    print("=" * 60)
    print(f"Grid 維度:    {get_cell_dim()}x{get_cell_dim()}x{get_cell_dim()}")
    print(f"單元格大小:   {get_cell_size()} m")
    print(f"起始高度:     {get_start_height()} m")
    print(f"子步驟數:     {get_sim_substeps()}")
    print("\n--- Gmsh 設定 ---")
    print(f"Remesh:       {get_remesh_mode()}")
    print(f"局部密度:     {get_use_local_density()}")
    print(f"邊界層:       {get_bl_enabled()}")
    print(f"優化:         {get_gmsh_optimize()}")
    print(f"快取目錄:     {cache_dir}")
    print("=" * 60 + "\n")


# ============================================================
# 插件資訊
# ============================================================

ADDON_VERSION = (1, 3, 0)
ADDON_NAME = "Warp Physics Simulation (Gmsh)"
ADDON_AUTHOR = "Your Name"
ADDON_DESCRIPTION = "GPU-accelerated soft body physics with Gmsh tetrahedral meshing"


# ============================================================
# 初始化
# ============================================================

try:
    initialize_cache_directory()
except Exception as e:
    print(f"⚠️ 快取目錄初始化失敗: {e}")
    cache_dir = None