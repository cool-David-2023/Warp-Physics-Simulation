"""
場景設置 - 負責創建相機、燈光、地面等場景元素
"""

import bpy
import math


def setup_scene():
    """設置完整場景（相機 + 燈光 + 地面）"""
    print("設置場景...")
    
    create_ground_plane()
    create_camera()
    create_light()
    
    print("✅ 場景設置完成")


def create_ground_plane(size=10.0, location=(0, 0, 0)):
    """
    創建地面平面
    
    Args:
        size: 平面大小
        location: 位置 (x, y, z)
    
    Returns:
        bpy.types.Object: 地面物件
    """
    # 創建平面
    bpy.ops.mesh.primitive_plane_add(size=size, location=location)
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    # 設置為線框顯示（避免遮擋）
    ground.display_type = 'WIRE'
    
    # 添加材質（可選）
    mat = bpy.data.materials.new(name="GroundMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.3, 0.3, 0.3, 1.0)  # 灰色
        bsdf.inputs["Roughness"].default_value = 0.8
    
    if ground.data.materials:
        ground.data.materials[0] = mat
    else:
        ground.data.materials.append(mat)
    
    print(f"✅ 地面已創建: {ground.name}")
    
    return ground


def create_camera(location=(5, -5, 4), rotation_euler=None):
    """
    創建相機
    
    Args:
        location: 相機位置 (x, y, z)
        rotation_euler: 歐拉角旋轉 (x, y, z) 弧度，None 則自動計算
    
    Returns:
        bpy.types.Object: 相機物件
    """
    # 創建相機
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.active_object
    camera.name = "Camera"
    
    # 設置旋轉（預設朝向場景中心）
    if rotation_euler is None:
        # 自動計算朝向原點的旋轉
        rotation_euler = (
            math.radians(63),     # X 軸旋轉（俯視角度）
            0,                    # Y 軸旋轉
            math.radians(45)      # Z 軸旋轉（45度側視）
        )
    
    camera.rotation_euler = rotation_euler
    
    # 設置為活動相機
    bpy.context.scene.camera = camera
    
    # 相機設定
    camera.data.lens = 50  # 焦距 50mm
    camera.data.clip_end = 1000  # 遠剪裁面
    
    print(f"✅ 相機已創建: {camera.name}")
    
    return camera


def create_light(light_type='SUN', location=(5, 5, 10), energy=1.0):
    """
    創建燈光
    
    Args:
        light_type: 燈光類型 ('SUN', 'POINT', 'SPOT', 'AREA')
        location: 燈光位置 (x, y, z)
        energy: 燈光強度
    
    Returns:
        bpy.types.Object: 燈光物件
    """
    # 創建燈光
    bpy.ops.object.light_add(type=light_type, location=location)
    light = bpy.context.active_object
    light.name = f"Light_{light_type}"
    
    # 設置燈光參數
    light.data.energy = energy
    
    # 根據類型設置特定參數
    if light_type == 'SUN':
        light.data.angle = math.radians(5)  # 太陽光角度
        light.rotation_euler = (
            math.radians(45),
            0,
            math.radians(30)
        )
    elif light_type == 'POINT':
        light.data.shadow_soft_size = 0.5
    
    print(f"✅ 燈光已創建: {light.name} ({light_type})")
    
    return light


def create_reference_grid(size=10, divisions=10):
    """
    創建參考網格（用於空間定位）
    
    Args:
        size: 網格大小
        divisions: 網格劃分數
    
    Returns:
        bpy.types.Object: 網格物件
    """
    # 創建平面並細分
    bpy.ops.mesh.primitive_plane_add(size=size)
    grid = bpy.context.active_object
    grid.name = "ReferenceGrid"
    
    # 添加細分修改器
    mod = grid.modifiers.new(name="Subdivision", type='SUBSURF')
    mod.levels = 0
    mod.render_levels = 0
    
    # 設置為線框顯示
    grid.display_type = 'WIRE'
    
    # 設置顏色（淺灰色）
    grid.color = (0.5, 0.5, 0.5, 0.3)
    
    print(f"✅ 參考網格已創建")
    
    return grid


def setup_world_lighting(strength=0.5, color=(1.0, 1.0, 1.0)):
    """
    設置世界環境光照
    
    Args:
        strength: 環境光強度
        color: 環境光顏色 RGB
    """
    world = bpy.context.scene.world
    
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    
    # 獲取背景節點
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (*color, 1.0)
        bg_node.inputs["Strength"].default_value = strength
    
    print(f"✅ 世界環境光已設置 (強度: {strength})")


def setup_viewport_shading(shading_type='SOLID'):
    """
    設置視窗著色模式
    
    Args:
        shading_type: 著色類型 ('WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED')
    """
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = shading_type
                    print(f"✅ 視窗著色模式設為: {shading_type}")
                    break


def set_frame_range(start=1, end=250):
    """
    設置時間軸範圍
    
    Args:
        start: 起始幀
        end: 結束幀
    """
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    scene.frame_current = start
    
    print(f"✅ 時間軸範圍設為: {start}-{end}")