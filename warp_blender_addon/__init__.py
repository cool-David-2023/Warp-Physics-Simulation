"""
Warp Physics Simulation - Blender 插件
GPU 加速的軟體體物理模擬，支援 Gmsh 四面體化
"""

bl_info = {
    "name": "Warp Physics Simulation (Gmsh)",
    "author": "cool-David-2023",
    "version": (1, 3, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Warp",
    "description": "GPU-accelerated soft body physics with Gmsh tetrahedral meshing",
    "category": "Physics",
    "doc_url": "https://github.com/cool-David-2023/Warp-Physics-Simulation",
}


# ============================================================
# 檢查依賴
# ============================================================

import sys

def check_dependencies():
    """檢查必要的 Python 套件"""
    missing_packages = []
    optional_packages = []
    
    # 必要套件
    try:
        import warp
        print(f"✓ Warp 版本: {warp.__version__}")
    except ImportError:
        missing_packages.append("warp-lang")
    
    try:
        import numpy
        print(f"✓ NumPy 版本: {numpy.__version__}")
    except ImportError:
        missing_packages.append("numpy")
    
    # Gmsh（必要）
    try:
        import gmsh
        print(f"✓ Gmsh 版本: {gmsh.__version__}")
    except ImportError:
        missing_packages.append("gmsh")
    
    # SciPy（可選，局部密度功能需要）
    try:
        import scipy
        print(f"✓ SciPy 版本: {scipy.__version__}")
    except ImportError:
        optional_packages.append("scipy")
        print("⚠ SciPy 未安裝（局部密度功能不可用）")
    
    if missing_packages:
        print("\n" + "=" * 60)
        print("❌ 缺少必要套件！請在 Blender Python 環境中安裝：")
        print("=" * 60)
        for pkg in missing_packages:
            print(f"   pip install {pkg}")
        print("=" * 60 + "\n")
        return False
    
    if optional_packages:
        print("\n提示：安裝 SciPy 以啟用局部密度分析:")
        for pkg in optional_packages:
            print(f"   pip install {pkg}")
    
    return True


# 檢查依賴
if not check_dependencies():
    def register():
        print("❌ Warp Physics Simulation (Gmsh): 缺少依賴套件，插件未載入")
    
    def unregister():
        pass
else:
    # ============================================================
    # 導入模組
    # ============================================================
    
    import bpy
    
    # 導入配置
    from . import config
    
    # 導入 UI
    from .ui.panel_main import (
        WARP_OT_OpenMaterialLibrary,
        WARP_OT_ApplyPreset,
        WARP_OT_SavePreset,
        WARP_OT_ResetParameters,
        WARP_PT_SimulationPanel,
        WARP_PT_GmshPanel,
        WARP_PT_GridPanel,
        WARP_PT_BakePanel,
        WARP_PT_StatusPanel,
    )
    
    # 導入 Operators
    from .operators.op_initialize import WARP_OT_InitModel
    from .operators.op_gmsh import WARP_OT_GenerateGmsh
    from .operators.op_init_from_tet import WARP_OT_InitFromTet
    from .operators.op_bake import WARP_OT_Bake
    from .operators.op_cache import WARP_OT_ClearCache, WARP_OT_LoadCache
    
    # 導入 Blender Integration
    from .blender_integration.frame_handler import unregister_frame_handler
    
    
    # ============================================================
    # 註冊類別列表
    # ============================================================
    
    classes = (
        # UI Operators
        WARP_OT_OpenMaterialLibrary,
        WARP_OT_ApplyPreset,
        WARP_OT_SavePreset,
        WARP_OT_ResetParameters,
        
        # Simulation Operators
        WARP_OT_InitModel,
        WARP_OT_GenerateGmsh,
        WARP_OT_InitFromTet,
        WARP_OT_Bake,
        WARP_OT_ClearCache,
        WARP_OT_LoadCache,
        
        # UI Panels
        WARP_PT_SimulationPanel,
        WARP_PT_GmshPanel,
        WARP_PT_GridPanel,
        WARP_PT_BakePanel,
        WARP_PT_StatusPanel,
    )
    
    
    # ============================================================
    # 註冊函數
    # ============================================================
    
    def register():
        """註冊插件"""
        print("\n" + "=" * 60)
        print("Warp Physics Simulation (Gmsh) 正在載入...")
        print("=" * 60)
        
        # 註冊所有類別
        for cls in classes:
            try:
                bpy.utils.register_class(cls)
                print(f"✓ 已註冊: {cls.__name__}")
            except Exception as e:
                print(f"✗ 註冊失敗: {cls.__name__} - {e}")
        
        # 註冊 UI 自定義屬性
        from .ui import panel_main
        panel_main.register()
        
        # 列印配置資訊
        config.print_config()
        
        print("=" * 60)
        print("✓ Warp Physics Simulation (Gmsh) 已載入")
        print("  請在 3D Viewport 側邊欄找到 'Warp' 標籤")
        print("=" * 60 + "\n")
    
    
    def unregister():
        """反註冊插件"""
        print("\n" + "=" * 60)
        print("Warp Physics Simulation (Gmsh) 正在卸載...")
        print("=" * 60)
        
        # 移除 Frame Handler
        unregister_frame_handler()
        
        # 反註冊 UI 自定義屬性
        from .ui import panel_main
        panel_main.unregister()
        
        # 反註冊所有類別（逆序）
        for cls in reversed(classes):
            try:
                bpy.utils.unregister_class(cls)
                print(f"✓ 已反註冊: {cls.__name__}")
            except Exception as e:
                print(f"✗ 反註冊失敗: {cls.__name__} - {e}")
        
        # 重置全域狀態
        config.reset_global_state()
        
        print("=" * 60)
        print("✓ Warp Physics Simulation (Gmsh) 已卸載")
        print("=" * 60 + "\n")


# ============================================================
# 直接執行測試（開發用）
# ============================================================

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    
    register()
    

    print("\n開發模式：插件已重新載入")
