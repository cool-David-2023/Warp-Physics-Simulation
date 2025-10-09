"""
Grid 生成操作器 - 創建規則網格四面體
生成虛擬物件並加入 Collection
"""

import bpy
import numpy as np
from .. import config


class WARP_OT_GenerateGrid(bpy.types.Operator):
    """生成規則 Grid 四面體網格"""
    
    bl_idname = "warp.generate_grid"
    bl_label = "Generate Grid"
    bl_description = "Generate regular grid tetrahedra"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """執行 Grid 生成"""
        print("\n" + "=" * 60)
        print("🎲 Grid 生成")
        print("=" * 60)
        
        try:
            # 1. 讀取參數
            cell_dim = config.get_cell_dim()
            cell_size = config.get_cell_size()
            start_height = config.get_start_height()
            
            print(f"Grid 維度: {cell_dim}x{cell_dim}x{cell_dim}")
            print(f"單元格大小: {cell_size}m")
            print(f"起始高度: {start_height}m")
            
            # 2. 創建虛擬物件
            grid_obj = self._create_grid_object(context, cell_dim, cell_size, start_height)
            
            # 3. 初始化材質屬性
            config.simulation_config.initialize_object_material(grid_obj)
            
            # 4. 標記為 Grid 類型
            grid_obj["warp_tet_type"] = "grid"
            grid_obj["warp_cell_dim"] = cell_dim
            grid_obj["warp_cell_size"] = cell_size
            grid_obj["warp_start_height"] = start_height
            
            # 5. 加入 Collection
            collection = context.scene.warp_collection
            if collection is None:
                # 創建新 Collection
                collection = bpy.data.collections.new("WarpCollection")
                context.scene.collection.children.link(collection)
                context.scene.warp_collection = collection
                print("✅ 已創建 WarpCollection")
            
            # 將物件加入 Collection
            if grid_obj.name not in collection.objects:
                collection.objects.link(grid_obj)
                # 從場景 Collection 中移除（避免重複）
                if grid_obj.name in context.scene.collection.objects:
                    context.scene.collection.objects.unlink(grid_obj)
            
            print(f"✅ Grid 物件已創建並加入 Collection: {grid_obj.name}")
            print("=" * 60 + "\n")
            
            self.report({'INFO'}, f"Grid 已生成: {grid_obj.name}")
            return {'FINISHED'}
            
        except Exception as e:
            print(f"❌ Grid 生成失敗: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Grid 生成失敗: {str(e)}")
            return {'CANCELLED'}
    
    def _create_grid_object(self, context, cell_dim, cell_size, start_height):
        """創建 Grid 虛擬物件（用 Cube 代表）"""
        # 計算 Grid 的實際大小
        grid_size = cell_dim * cell_size
        
        # 創建一個立方體代表 Grid
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,  # 單位大小
            location=(0, 0, 0)  # 原點
        )
        
        grid_obj = context.active_object
        grid_obj.name = "GridSoftBody"
        
        # 縮放到正確大小
        grid_obj.scale = (grid_size, grid_size, grid_size)
        
        # 移動到起始高度（Z 軸方向，因為 Blender 是 Z-up）
        grid_obj.location = (0, 0, start_height)
        
        # 設置顯示
        grid_obj.display_type = 'WIRE'
        grid_obj.color = (0.2, 1.0, 0.2, 1.0)  # 綠色
        
        return grid_obj