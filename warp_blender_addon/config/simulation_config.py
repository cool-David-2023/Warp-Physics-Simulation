"""
Simulation Config - 模擬參數配置
包含材質預設、模擬品質、接觸參數等
"""

import bpy


# ============================================================
# 材質預設組
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

# Grid 網格設定
DEFAULT_CELL_DIM = 4
DEFAULT_CELL_SIZE = 0.4
DEFAULT_START_HEIGHT = 2.0

# 材質參數（預設值，物件可覆蓋）
DEFAULT_DENSITY = 100.0
DEFAULT_K_MU = 1000.0
DEFAULT_K_LAMBDA = 5000.0
DEFAULT_K_DAMP = 0.5

# 模擬品質
DEFAULT_SIM_SUBSTEPS = 32

# 接觸參數
DEFAULT_CONTACT_KE = 1.0e3   # 接觸剛度
DEFAULT_CONTACT_KD = 0.0     # 接觸阻尼
DEFAULT_CONTACT_KF = 1.0e3   # 摩擦力剛度
DEFAULT_CONTACT_MU = 0.5     # 摩擦係數


# ============================================================
# 參數讀取函數（Grid）
# ============================================================

def get_cell_dim():
    """讀取 Grid 網格維度"""
    try:
        return bpy.context.scene.warp_cell_dim
    except:
        return DEFAULT_CELL_DIM

def get_cell_size():
    """讀取 Grid 單元格大小"""
    try:
        return bpy.context.scene.warp_cell_size
    except:
        return DEFAULT_CELL_SIZE

def get_start_height():
    """讀取 Grid 起始高度"""
    try:
        return bpy.context.scene.warp_start_height
    except:
        return DEFAULT_START_HEIGHT

def get_sim_substeps():
    """讀取模擬子步驟數"""
    try:
        return bpy.context.scene.warp_sim_substeps
    except:
        return DEFAULT_SIM_SUBSTEPS


# ============================================================
# 物件材質參數讀取（從 Custom Properties）
# ============================================================

def get_object_density(obj):
    """讀取物件密度"""
    return obj.get("warp_density", DEFAULT_DENSITY)

def get_object_k_mu(obj):
    """讀取物件剪切模量"""
    return obj.get("warp_k_mu", DEFAULT_K_MU)

def get_object_k_lambda(obj):
    """讀取物件體積模量"""
    return obj.get("warp_k_lambda", DEFAULT_K_LAMBDA)

def get_object_k_damp(obj):
    """讀取物件阻尼"""
    return obj.get("warp_k_damp", DEFAULT_K_DAMP)

def get_object_contact_ke(obj):
    """讀取物件接觸剛度"""
    return obj.get("warp_contact_ke", DEFAULT_CONTACT_KE)

def get_object_contact_kd(obj):
    """讀取物件接觸阻尼"""
    return obj.get("warp_contact_kd", DEFAULT_CONTACT_KD)

def get_object_contact_kf(obj):
    """讀取物件摩擦力剛度"""
    return obj.get("warp_contact_kf", DEFAULT_CONTACT_KF)

def get_object_contact_mu(obj):
    """讀取物件摩擦係數"""
    return obj.get("warp_contact_mu", DEFAULT_CONTACT_MU)


# ============================================================
# 物件材質參數設置（到 Custom Properties）
# ============================================================

def set_object_density(obj, value):
    """設置物件密度"""
    obj["warp_density"] = float(value)

def set_object_k_mu(obj, value):
    """設置物件剪切模量"""
    obj["warp_k_mu"] = float(value)

def set_object_k_lambda(obj, value):
    """設置物件體積模量"""
    obj["warp_k_lambda"] = float(value)

def set_object_k_damp(obj, value):
    """設置物件阻尼"""
    obj["warp_k_damp"] = float(value)

def set_object_contact_ke(obj, value):
    """設置物件接觸剛度"""
    obj["warp_contact_ke"] = float(value)

def set_object_contact_kd(obj, value):
    """設置物件接觸阻尼"""
    obj["warp_contact_kd"] = float(value)

def set_object_contact_kf(obj, value):
    """設置物件摩擦力剛度"""
    obj["warp_contact_kf"] = float(value)

def set_object_contact_mu(obj, value):
    """設置物件摩擦係數"""
    obj["warp_contact_mu"] = float(value)


# ============================================================
# 批量操作
# ============================================================

def apply_preset_to_object(obj, preset_key):
    """套用材質預設到物件"""
    if preset_key not in PRESETS:
        return False
    
    preset = PRESETS[preset_key]
    set_object_k_mu(obj, preset['k_mu'])
    set_object_k_lambda(obj, preset['k_lambda'])
    set_object_k_damp(obj, preset['k_damp'])
    set_object_density(obj, preset['density'])
    
    return True

def initialize_object_material(obj):
    """初始化物件材質參數（如果不存在）"""
    if "warp_density" not in obj:
        set_object_density(obj, DEFAULT_DENSITY)
    if "warp_k_mu" not in obj:
        set_object_k_mu(obj, DEFAULT_K_MU)
    if "warp_k_lambda" not in obj:
        set_object_k_lambda(obj, DEFAULT_K_LAMBDA)
    if "warp_k_damp" not in obj:
        set_object_k_damp(obj, DEFAULT_K_DAMP)
    if "warp_contact_ke" not in obj:
        set_object_contact_ke(obj, DEFAULT_CONTACT_KE)
    if "warp_contact_kd" not in obj:
        set_object_contact_kd(obj, DEFAULT_CONTACT_KD)
    if "warp_contact_kf" not in obj:
        set_object_contact_kf(obj, DEFAULT_CONTACT_KF)
    if "warp_contact_mu" not in obj:
        set_object_contact_mu(obj, DEFAULT_CONTACT_MU)