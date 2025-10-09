"""
統一初始化操作器 - 支援多物件、Grid + Gmsh 混合
讀取 Collection 內所有啟用物件並初始化
"""

import bpy
import numpy as np
import warp as wp
import warp.sim
from .. import config
from ..core.coordinate_utils import blender_to_warp, get_rotation_quaternion
from ..blender_integration.mesh_builder import create_wireframe_mesh


class WARP_OT_Initialize(bpy.types.Operator):
    """初始化 Warp 物理模擬（多物件）"""
    
    bl_idname = "warp.initialize"
    bl_label = "Initialize Simulation"
    bl_description = "Initialize Warp simulation from all enabled objects in collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """執行初始化"""
        print("\n" + "=" * 60)
        print("🚀 初始化 Warp 多物件模擬")
        print("=" * 60)
        
        try:
            # 1. 檢查 Collection
            collection = context.scene.warp_collection
            if collection is None:
                self.report({'ERROR'}, "請選擇 Collection")
                return {'CANCELLED'}
            
            # 2. 獲取啟用的物件
            enabled_objects = [
                obj for obj in collection.all_objects
                if obj.get("warp_enabled", True)
            ]
            
            if len(enabled_objects) == 0:
                self.report({'ERROR'}, "Collection 內無啟用物件")
                return {'CANCELLED'}
            
            print(f"📦 Collection: {collection.name}")
            print(f"✅ 啟用物件: {len(enabled_objects)}")
            
            # 3. 創建 ModelBuilder
            builder = wp.sim.ModelBuilder()
            particle_offset = 0
            
            # 4. 遍歷所有啟用物件
            for obj in enabled_objects:
                print(f"\n🔧 處理物件: {obj.name}")
                
                # 讀取物件材質
                material = config.get_object_material(obj)
                
                # 判斷類型：Grid 或 Mesh
                tet_type = obj.get("warp_tet_type", "mesh")
                
                if tet_type == "grid":
                    # Grid 類型
                    particle_count = self._add_grid_to_builder(builder, obj, material)
                else:
                    # Mesh 類型
                    particle_count = self._add_mesh_to_builder(builder, obj, material)
                
                if particle_count is None:
                    self.report({'ERROR'}, f"物件 {obj.name} 初始化失敗")
                    return {'CANCELLED'}
                
                # 記錄粒子範圍
                config.cache_info['objects'][obj.name] = {
                    'particle_count': particle_count,
                    'particle_offset': particle_offset,
                    'particle_end': particle_offset + particle_count
                }
                
                particle_offset += particle_count
                
                print(f"   ✅ 粒子: {particle_count}")
            
            # 5. 添加地面
            builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0))
            
            # 6. Finalize Model
            print(f"\n🔨 Finalize Model...")
            config.model = builder.finalize(device="cuda:0")
            
            # 7. 設置全域接觸參數
            self._setup_contact_parameters(context)
            
            # 8. 創建狀態
            config.state_0 = config.model.state()
            config.state_1 = config.model.state()
            config.integrator = wp.sim.SemiImplicitIntegrator()
            
            print(f"\n✅ Model 已創建")
            print(f"   總粒子數: {config.model.particle_count}")
            print(f"   總四面體數: {config.model.tet_count}")
            
            # 9. 創建線框（每個物件一個）
            self._create_wireframes(enabled_objects)
            
            # 10. 更新快取資訊
            config.cache_info['fps'] = context.scene.render.fps
            config.cache_info['baked'] = False
            
            # 11. 設置到起始幀
            context.scene.frame_set(context.scene.frame_start)
            
            print("=" * 60)
            print("✅ 初始化完成！")
            print("=" * 60 + "\n")
            
            self.report({'INFO'}, f"初始化成功：{len(enabled_objects)} 物件")
            return {'FINISHED'}
            
        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"初始化失敗: {str(e)}")
            return {'CANCELLED'}
    
    def _add_grid_to_builder(self, builder, obj, material):
        """添加 Grid 到 builder"""
        # 讀取 Grid 參數
        cell_dim = obj.get("warp_cell_dim", config.DEFAULT_CELL_DIM)
        cell_size = obj.get("warp_cell_size", config.DEFAULT_CELL_SIZE)
        start_height = obj.get("warp_start_height", config.DEFAULT_START_HEIGHT)
        
        print(f"   類型: Grid ({cell_dim}³)")
        
        # 旋轉四元數
        rot_quat = get_rotation_quaternion()
        
        builder.add_soft_grid(
            pos=wp.vec3(0.0, start_height, 0.0),
            rot=rot_quat,
            vel=wp.vec3(0.0, 0.0, 0.0),
            dim_x=cell_dim,
            dim_y=cell_dim,
            dim_z=cell_dim,
            cell_x=cell_size,
            cell_y=cell_size,
            cell_z=cell_size,
            density=material['density'],
            k_mu=material['k_mu'],
            k_lambda=material['k_lambda'],
            k_damp=material['k_damp']
        )
        
        # 返回粒子數
        return (cell_dim + 1) ** 3
    
    def _add_mesh_to_builder(self, builder, obj, material):
        """添加 Mesh 到 builder"""
        # 從 config 讀取四面體數據
        tet_data = config.object_tet_data.get(obj.name)
        
        if tet_data is None:
            print(f"   ❌ 找不到四面體數據")
            return None
        
        vertices_blender = tet_data['vertices']
        elements = tet_data['elements']
        
        print(f"   類型: Mesh ({len(elements)} tets)")
        
        # 座標轉換 Blender → Warp
        vertices_warp = np.column_stack([
            vertices_blender[:, 0],
            vertices_blender[:, 2],
            vertices_blender[:, 1]
        ]).astype(np.float32)
        
        # 檢查並修正反轉四面體
        vertices_warp, elements = self._ensure_positive_volumes(vertices_warp, elements)
        
        # 轉換為 List[List[float]]
        vertices_list = vertices_warp.tolist()
        indices_list = elements.flatten().tolist()
        
        # 添加到 builder
        builder.add_soft_mesh(
            pos=(0.0, 0.0, 0.0),
            rot=(0.0, 0.0, 0.0, 1.0),
            vel=(0.0, 0.0, 0.0),
            vertices=vertices_list,
            indices=indices_list,
            density=material['density'],
            k_mu=material['k_mu'],
            k_lambda=material['k_lambda'],
            k_damp=material['k_damp'],
            scale=1.0,
            tri_ke=0.0,
            tri_ka=1e-8,
            tri_kd=0.0,
            tri_drag=0.0,
            tri_lift=0.0
        )
        
        # 返回粒子數
        return len(vertices_warp)
    
    def _ensure_positive_volumes(self, vertices_warp, elements):
        """確保所有四面體體積為正"""
        from ..core.mesh_validator import MeshValidator
        
        validator = MeshValidator()
        volumes = validator.compute_tet_volumes(vertices_warp, elements)
        
        invalid_count = np.sum(volumes <= 0)
        
        if invalid_count > 0:
            print(f"   ⚠️ 檢測到 {invalid_count} 個反轉四面體，正在修正...")
            
            # 如果全部反轉，交換索引
            if np.all(volumes <= 0):
                elements = elements[:, [1, 0, 2, 3]]
                volumes = validator.compute_tet_volumes(vertices_warp, elements)
                invalid_count = np.sum(volumes <= 0)
                print(f"   → 修正後反轉數: {invalid_count}")
        
        return vertices_warp, elements
    
    def _setup_contact_parameters(self, context):
        """設置全域接觸參數"""
        scene = context.scene
        
        # 從 Scene 屬性讀取（全域）
        config.model.soft_contact_ke = scene.warp_contact_ke
        config.model.soft_contact_kd = scene.warp_contact_kd
        config.model.soft_contact_kf = scene.warp_contact_kf
        config.model.soft_contact_mu = scene.warp_contact_mu
        config.model.ground = True
        
        print(f"\n🔗 接觸參數（全域）:")
        print(f"   Contact Stiffness: {config.model.soft_contact_ke}")
        print(f"   Contact Damping: {config.model.soft_contact_kd}")
        print(f"   Friction Stiffness: {config.model.soft_contact_kf}")
        print(f"   Friction Coefficient: {config.model.soft_contact_mu}")
    
    def _create_wireframes(self, objects):
        """為每個物件創建線框"""
        print(f"\n🎨 創建線框...")
        
        for obj in objects:
            obj_info = config.cache_info['objects'][obj.name]
            particle_offset = obj_info['particle_offset']
            particle_count = obj_info['particle_count']
            
            # 獲取該物件的粒子位置
            all_positions = config.state_0.particle_q.numpy()
            obj_positions = all_positions[particle_offset:particle_offset + particle_count]
            
            # 獲取四面體索引
            tet_type = obj.get("warp_tet_type", "mesh")
            
            if tet_type == "grid":
                # Grid: 從 model 提取對應範圍的 tet_indices
                # 簡化：直接使用物件本身作為線框（因為是 WIRE 模式）
                config.wireframe_objects[obj.name] = obj
                print(f"   {obj.name}: 使用物件本身（Grid）")
            else:
                # Mesh: 創建線框
                tet_data = config.object_tet_data.get(obj.name)
                if tet_data:
                    tet_indices = tet_data['elements']
                    wireframe_obj = create_wireframe_mesh(obj_positions, tet_indices)
                    wireframe_obj.name = f"{obj.name}_Wire"
                    config.wireframe_objects[obj.name] = wireframe_obj
                    print(f"   {obj.name}: 創建線框 ({len(tet_indices)} tets)")
                else:
                    print(f"   ⚠️ {obj.name}: 找不到四面體數據")
        
        print(f"✅ 線框創建完成")