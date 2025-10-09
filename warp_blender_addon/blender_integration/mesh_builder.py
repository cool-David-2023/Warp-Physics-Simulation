"""
網格構建器 - 負責創建和更新 Blender 網格物件
主要處理線框顯示和頂點更新
"""

import bpy
import numpy as np
from ..core.coordinate_utils import warp_to_blender


def extract_edges_from_tets(tet_indices):
    """
    從四面體索引提取所有唯一的邊
    
    Args:
        tet_indices: 四面體索引數組 (N, 4)，每個四面體有 4 個頂點
    
    Returns:
        list: 唯一邊的列表 [(v1, v2), ...]
    """
    edges_set = set()
    
    # 四面體的 6 條邊（4個頂點兩兩組合）
    edge_patterns = [
        (0, 1), (0, 2), (0, 3),  # 從頂點 0 出發
        (1, 2), (1, 3),          # 從頂點 1 出發
        (2, 3)                   # 從頂點 2 出發
    ]
    
    # 遍歷所有四面體
    for tet in tet_indices:
        for i, j in edge_patterns:
            # 確保邊的方向統一（小索引在前）
            edge = tuple(sorted([tet[i], tet[j]]))
            edges_set.add(edge)
    
    edges_list = list(edges_set)
    print(f"✅ 從 {len(tet_indices)} 個四面體提取了 {len(edges_list)} 條唯一邊")
    
    return edges_list


def update_grid_vertices(obj, positions_warp):
    """
    更新 Grid 物件的頂點位置
    
    Args:
        obj: Blender Grid 物件
        positions_warp: Warp 座標系的粒子位置 (N, 3)
    """
    if obj is None or obj.data is None:
        return
    
    mesh = obj.data
    
    # 檢查頂點數量
    if len(positions_warp) != len(mesh.vertices):
        print(f"⚠️ Grid 頂點數量不匹配: {len(positions_warp)} vs {len(mesh.vertices)}")
        # Grid 物件只是代表，不更新頂點
        return
    
    # 批量轉換座標
    from ..core.coordinate_utils import warp_to_blender
    positions_blender = warp_to_blender(positions_warp)
    
    # 更新頂點
    coords_flat = positions_blender.flatten()
    mesh.vertices.foreach_set("co", coords_flat)
    mesh.update()

def create_wireframe_mesh(positions_warp, tet_indices):
    """
    創建線框網格物件
    
    Args:
        positions_warp: Warp 座標系的粒子位置 (N, 3) numpy array
        tet_indices: 四面體索引 (M, 4) numpy array
    
    Returns:
        bpy.types.Object: 創建的線框物件
    """
    print(f"創建線框網格...")
    print(f"   - 頂點數: {len(positions_warp)}")
    
    # 1. 提取邊
    edges = extract_edges_from_tets(tet_indices)
    
    # 2. 轉換座標系
    if isinstance(positions_warp, np.ndarray) and positions_warp.ndim == 2:
        # 批量轉換
        positions_blender = warp_to_blender(positions_warp)
    else:
        # 逐個轉換
        positions_blender = [warp_to_blender(pos) for pos in positions_warp]
    
    # 3. 創建網格數據
    mesh = bpy.data.meshes.new("WarpWireframe")
    mesh.from_pydata(
        vertices=positions_blender,
        edges=edges,
        faces=[]  # 純線框，無面
    )
    mesh.update()
    
    # 4. 創建物件並連接到場景
    obj = bpy.data.objects.new("WarpWireframe", mesh)
    bpy.context.collection.objects.link(obj)
    
    # 5. 設置顯示模式為線框
    obj.display_type = 'WIRE'
    
    # 6. 設置線框顏色（可選）
    obj.color = (0.2, 0.6, 1.0, 1.0)  # 淺藍色
    
    print(f"✅ 線框物件已創建: {obj.name}")
    print(f"   - 邊數: {len(edges)}")
    
    return obj


def update_wireframe_mesh(obj, positions_warp):
    """
    更新線框網格的頂點位置（高效版本）
    
    Args:
        obj: Blender 物件
        positions_warp: Warp 座標系的粒子位置 (N, 3) numpy array
    """
    if obj is None or obj.data is None:
        print("⚠️ 無效的線框物件")
        return
    
    mesh = obj.data
    
    # 檢查頂點數量是否匹配
    if len(positions_warp) != len(mesh.vertices):
        print(f"⚠️ 頂點數量不匹配: {len(positions_warp)} vs {len(mesh.vertices)}")
        return
    
    # 批量轉換座標
    if isinstance(positions_warp, np.ndarray) and positions_warp.ndim == 2:
        positions_blender = warp_to_blender(positions_warp)
    else:
        positions_blender = [warp_to_blender(pos) for pos in positions_warp]
    
    # 高效更新頂點座標
    # 使用 foreach_set 比逐個設置快 10-100 倍
    if isinstance(positions_blender, np.ndarray):
        # NumPy 數組可直接 flatten
        coords_flat = positions_blender.flatten()
    else:
        # List 需要手動展開
        coords_flat = []
        for pos in positions_blender:
            coords_flat.extend(pos)
    
    mesh.vertices.foreach_set("co", coords_flat)
    
    # 更新網格（不重新計算法線，因為是線框）
    mesh.update()


def create_mesh_from_surface(positions_warp, tri_indices):
    """
    從表面三角形創建實體網格（預留功能）
    
    Args:
        positions_warp: Warp 座標系的粒子位置 (N, 3)
        tri_indices: 三角形索引 (M, 3)
    
    Returns:
        bpy.types.Object: 創建的網格物件
    """
    print(f"創建表面網格...")
    
    # 轉換座標系
    if isinstance(positions_warp, np.ndarray) and positions_warp.ndim == 2:
        positions_blender = warp_to_blender(positions_warp)
    else:
        positions_blender = [warp_to_blender(pos) for pos in positions_warp]
    
    # 創建網格
    mesh = bpy.data.meshes.new("WarpSurface")
    mesh.from_pydata(
        vertices=positions_blender,
        edges=[],
        faces=tri_indices.tolist()
    )
    mesh.update()
    
    # 計算法線
    mesh.calc_normals()
    
    # 創建物件
    obj = bpy.data.objects.new("WarpSurface", mesh)
    bpy.context.collection.objects.link(obj)
    
    # 設置平滑著色
    for face in mesh.polygons:
        face.use_smooth = True
    
    print(f"✅ 表面網格已創建: {obj.name}")
    
    return obj


def add_subdivision_modifier(obj, levels=2):
    """
    添加細分曲面修改器（用於平滑顯示）
    
    Args:
        obj: Blender 物件
        levels: 細分等級
    """
    if obj is None:
        return
    
    modifier = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    modifier.levels = levels
    modifier.render_levels = levels
    
    print(f"✅ 已添加細分修改器 (等級 {levels})")


def set_material(obj, color=(0.2, 0.6, 1.0, 1.0), metallic=0.0, roughness=0.5):
    """
    為物件設置材質（預留功能）
    
    Args:
        obj: Blender 物件
        color: RGBA 顏色
        metallic: 金屬度 [0, 1]
        roughness: 粗糙度 [0, 1]
    """
    if obj is None:
        return
    
    # 創建材質
    mat = bpy.data.materials.new(name="WarpMaterial")
    mat.use_nodes = True
    
    # 獲取 Principled BSDF 節點
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    
    # 分配材質
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    print(f"✅ 材質已設置")