"""
全域配置 - 集中管理所有常數、全域變數和設定
支援 Gmsh 進階功能：Remesh、局部密度、邊界層等
"""

import bpy
from pathlib import Path
import tempfile


# ============================================================
# 預設參數組
# ============================================================

PRESETS = {
    'SOFT_RUBBER': {
        'name': '軟橡膠 (Soft Rubber)',
        'k_mu': 1000.0,
        'k_lambda': 5000.0,
        'k_damp': 0.5,
        'density': 100.0,
    },
    'HARD_RUBBER': {
        'name': '硬橡膠 (Hard Rubber)',
        'k_mu': 5000.0,
        'k_lambda': 20000.0,
        'k_damp': 0.1,
        'density': 200.0,
    },
    'JELLY': {
        'name': '果凍 (Jelly)',
        'k_mu': 500.0,
        'k_lambda': 2000.0,
        'k_damp': 1.0,
        'density': 80.0,
    },
    'SOFT_FOAM': {
        'name': '軟泡棉 (Soft Foam)',
        'k_mu': 300.0,
        'k_lambda': 1000.0,
        'k_damp': 0.8,
        'density': 50.0,
    },
    'STIFF': {
        'name': '堅硬 (Stiff)',
        'k_mu': 10000.0,
        'k_lambda': 50000.0,
        'k_damp': 0.05,
        'density': 300.0,
    },
}


# ============================================================
# 預設模擬參數
# ============================================================

# 網格設定
DEFAULT_CELL_DIM = 4
DEFAULT_CELL_SIZE = 0.4
DEFAULT_START_HEIGHT = 2.0

# 材質參數
DEFAULT_DENSITY = 100.0
DEFAULT_K_MU = 1000.0
DEFAULT_K_LAMBDA = 5000.0
DEFAULT_K_DAMP = 0.0

# 模擬品質
DEFAULT_SIM_SUBSTEPS = 32

# 接觸參數（新增）
DEFAULT_CONTACT_KE = 1.0e3   # 接觸剛度
DEFAULT_CONTACT_KD = 0.0     # 接觸阻尼（零！）
DEFAULT_CONTACT_KF = 1.0e3   # 摩擦力剛度
DEFAULT_CONTACT_MU = 0.5     # 摩擦係數

# 重力
GRAVITY = -9.81

def get_contact_ke():
    try:
        return bpy.context.scene.warp_contact_ke
    except:
        return DEFAULT_CONTACT_KE

def get_contact_kd():
    try:
        return bpy.context.scene.warp_contact_kd
    except:
        return DEFAULT_CONTACT_KD

def get_contact_kf():
    try:
        return bpy.context.scene.warp_contact_kf
    except:
        return DEFAULT_CONTACT_KF

def get_contact_mu():
    try:
        return bpy.context.scene.warp_contact_mu
    except:
        return DEFAULT_CONTACT_MU
# ============================================================
# Gmsh 配置（新增）
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
# 動態參數讀取（原有）
# ============================================================

def get_cell_dim():
    try:
        return bpy.context.scene.warp_cell_dim
    except:
        return DEFAULT_CELL_DIM

def get_cell_size():
    try:
        return bpy.context.scene.warp_cell_size
    except:
        return DEFAULT_CELL_SIZE

def get_start_height():
    try:
        return bpy.context.scene.warp_start_height
    except:
        return DEFAULT_START_HEIGHT

def get_density():
    try:
        return bpy.context.scene.warp_density
    except:
        return DEFAULT_DENSITY

def get_k_mu():
    try:
        return bpy.context.scene.warp_k_mu
    except:
        return DEFAULT_K_MU

def get_k_lambda():
    try:
        return bpy.context.scene.warp_k_lambda
    except:
        return DEFAULT_K_LAMBDA

def get_k_damp():
    try:
        return bpy.context.scene.warp_k_damp
    except:
        return DEFAULT_K_DAMP

def get_sim_substeps():
    try:
        return bpy.context.scene.warp_sim_substeps
    except:
        return DEFAULT_SIM_SUBSTEPS


# ============================================================
# Gmsh 參數讀取（新增）
# ============================================================

def get_remesh_mode():
    try:
        return bpy.context.scene.warp_remesh_mode
    except:
        return DEFAULT_REMESH_MODE

def get_remesh_voxel_size():
    try:
        return bpy.context.scene.warp_remesh_voxel_size
    except:
        return DEFAULT_REMESH_VOXEL_SIZE

def get_remesh_octree_depth():
    try:
        return bpy.context.scene.warp_remesh_octree_depth
    except:
        return DEFAULT_REMESH_OCTREE_DEPTH

def get_use_local_density():
    try:
        return bpy.context.scene.warp_use_local_density
    except:
        return DEFAULT_USE_LOCAL_DENSITY

def get_blur_radius():
    try:
        return bpy.context.scene.warp_blur_radius
    except:
        return DEFAULT_BLUR_RADIUS

def get_outlier_removal():
    try:
        return bpy.context.scene.warp_outlier_removal
    except:
        return DEFAULT_OUTLIER_REMOVAL

def get_size_clamp_ratio():
    try:
        return bpy.context.scene.warp_size_clamp_ratio
    except:
        return DEFAULT_SIZE_CLAMP_RATIO

def get_bl_enabled():
    try:
        return bpy.context.scene.warp_bl_enabled
    except:
        return DEFAULT_BL_ENABLED

def get_bl_thickness():
    try:
        return bpy.context.scene.warp_bl_thickness
    except:
        return DEFAULT_BL_THICKNESS

def get_bl_size_multiplier():
    try:
        return bpy.context.scene.warp_bl_size_multiplier
    except:
        return DEFAULT_BL_SIZE_MULTIPLIER

def get_core_size_multiplier():
    try:
        return bpy.context.scene.warp_core_size_multiplier
    except:
        return DEFAULT_CORE_SIZE_MULTIPLIER

def get_algorithm_3d():
    try:
        # EnumProperty 返回字串，需轉換為整數
        return int(bpy.context.scene.warp_algorithm_3d)
    except:
        return DEFAULT_ALGORITHM_3D

def get_gmsh_optimize():
    try:
        return bpy.context.scene.warp_gmsh_optimize
    except:
        return DEFAULT_GMSH_OPTIMIZE

def get_optimize_iterations():
    try:
        return bpy.context.scene.warp_optimize_iterations
    except:
        return DEFAULT_OPTIMIZE_ITERATIONS

def get_gmsh_verbose():
    try:
        return bpy.context.scene.warp_gmsh_verbose
    except:
        return DEFAULT_GMSH_VERBOSE


# ============================================================
# 快取設定
# ============================================================

CACHE_DIR_NAME = "warp_cache"


# ============================================================
# 全域變數（模擬狀態）
# ============================================================

model = None
state_0 = None
state_1 = None
integrator = None
wireframe_object = None
cache_dir = None

# Gmsh 生成的線框物件（替換 tetgen_wireframe）
gmsh_wireframe = None
tet_data = None  # 存儲四面體數據

cache_info = {
    'frame_start': 1,
    'frame_end': 250,
    'particle_count': 0,
    'fps': 24,
    'baked': False
}


# ============================================================
# 輔助函數
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

def reset_global_state():
    """重置全域狀態"""
    global model, state_0, state_1, integrator, wireframe_object, gmsh_wireframe, tet_data
    
    model = None
    state_0 = None
    state_1 = None
    integrator = None
    wireframe_object = None
    gmsh_wireframe = None
    tet_data = None
    
    cache_info['baked'] = False
    cache_info['particle_count'] = 0

def get_simulation_info():
    """獲取模擬資訊"""
    return {
        'model_initialized': model is not None,
        'particle_count': model.particle_count if model else 0,
        'cache_baked': cache_info['baked'],
        'cache_dir': str(cache_dir) if cache_dir else None,
        'wireframe_exists': wireframe_object is not None,
        'gmsh_exists': gmsh_wireframe is not None,
        'tet_data_exists': tet_data is not None,
    }

def print_config():
    """列印當前配置"""
    print("\n" + "=" * 60)
    print("⚙️ Warp Simulation Configuration (Gmsh)")
    print("=" * 60)
    print(f"網格維度:     {get_cell_dim()}x{get_cell_dim()}x{get_cell_dim()}")
    print(f"單元格大小:   {get_cell_size()} m")
    print(f"初始高度:     {get_start_height()} m")
    print(f"密度:         {get_density()} kg/m³")
    print(f"剪切模量:     {get_k_mu()}")
    print(f"體積模量:     {get_k_lambda()}")
    print(f"阻尼係數:     {get_k_damp()}")
    print(f"子步驟數:     {get_sim_substeps()}")
    print("\n--- Gmsh 設定 ---")
    print(f"Remesh 模式:  {get_remesh_mode()}")
    print(f"局部密度:     {get_use_local_density()}")
    print(f"邊界層:       {get_bl_enabled()}")
    print(f"優化:         {get_gmsh_optimize()}")
    print(f"快取目錄:     {cache_dir}")
    print("=" * 60 + "\n")


# ============================================================
# 插件資訊
# ============================================================

ADDON_VERSION = (2, 0, 0)  # 升級到 2.0（Gmsh 版本）
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