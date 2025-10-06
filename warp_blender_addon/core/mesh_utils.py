"""
網格工具 - 處理 Blender 網格與 Warp 的轉換
"""

import bpy
import numpy as np
from ..core.coordinate_utils import blender_to_warp


def get_selected_mesh_data():
    """
    獲取選中的網格數據（頂點和四面體）
    
    Returns:
        tuple: (vertices, tet_indices) 或 None
            - vertices: numpy array (N, 3) Blender 座標系
            - tet_indices: numpy array (M, 4) 四面體索引
    """
    # 獲取活動物件
    obj = bpy.context.active_object
    
    if obj is None or obj.type != 'MESH':
        print("❌ 請選擇一個網格物件")
        return None
    
    mesh = obj.data
    
    # 獲取頂點位置（世界座標）
    vertices_blender = np.array([
        obj.matrix_world @ v.co for v in mesh.vertices
    ])
    
    print(f"✅ 已讀取網格: {obj.name}")
    print(f"   - 頂點數: {len(vertices_blender)}")
    
    # 檢查是否有四面體數據（需要外部四面體化）
    # 這裡先返回 None，表示需要使用其他方法生成四面體
    print("⚠️ 四面體數據需要外部工具生成（如 TetGen）")
    
    return vertices_blender, None


def tetrahedralize_mesh(vertices, method='delaunay'):
    """
    將網格四面體化（需要外部庫）
    
    Args:
        vertices: 頂點數組 (N, 3)
        method: 'delaunay' 或 'tetgen'
    
    Returns:
        tet_indices: 四面體索引 (M, 4) 或 None
    """
    print(f"⚠️ 四面體化功能需要安裝 scipy 或 tetgen")
    print("   推薦使用 Warp 的 add_soft_grid 生成規則網格")
    
    # 預留介面：未來可整合 scipy.spatial.Delaunay 或 tetgen
    return None


def validate_tet_mesh(vertices, tet_indices):
    """
    驗證四面體網格的有效性
    
    Args:
        vertices: 頂點數組 (N, 3)
        tet_indices: 四面體索引 (M, 4)
    
    Returns:
        bool: 是否有效
    """
    if vertices is None or tet_indices is None:
        return False
    
    # 檢查索引範圍
    max_index = np.max(tet_indices)
    if max_index >= len(vertices):
        print(f"❌ 四面體索引超出範圍: {max_index} >= {len(vertices)}")
        return False
    
    # 檢查四面體數量
    if tet_indices.shape[1] != 4:
        print(f"❌ 四面體應有 4 個頂點，但有 {tet_indices.shape[1]}")
        return False
    
    print(f"✅ 四面體網格有效: {len(tet_indices)} 個四面體")
    return True