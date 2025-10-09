"""
Gmsh 操作器 - 對選中物件執行四面體化並顯示線框
支援 Remesh、局部密度、邊界層等進階功能
"""

import bpy
import numpy as np
from .. import config
from ..core.gmsh_generator import GmshGenerator
from ..core.mesh_validator import MeshValidator


class WARP_OT_GenerateGmsh(bpy.types.Operator):
    """對選中物件執行 Gmsh 四面體化"""
    
    bl_idname = "warp.generate_gmsh"
    bl_label = "Generate Tetrahedra (Gmsh)"
    bl_description = "Generate tetrahedral mesh from selected object using Gmsh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """執行 Gmsh"""
        # 檢查選中物件
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "請選擇一個網格物件")
            return {'CANCELLED'}
        
        print("\n" + "=" * 60)
        print(f"🎯 Gmsh: {obj.name}")
        print("=" * 60)
        
        try:
            # 1. 創建臨時副本
            temp_obj = self._create_temp_copy(obj)
            
            # 2. Remesh（如果啟用）
            remesh_mode = config.get_remesh_mode()
            if remesh_mode != 'NONE':
                print(f"\n🔧 Remesh ({remesh_mode})...")
                self._apply_remesh(temp_obj, remesh_mode)
            
            # 3. 三角化
            print(f"🔧 三角化...")
            self._triangulate(temp_obj)
            
            # 4. 提取網格數據
            vertices_blender, faces = self._extract_mesh_data(temp_obj)
            
            print(f"\n處理後網格:")
            print(f"   頂點: {len(vertices_blender)}")
            print(f"   三角形: {len(faces)}")
            
            # 5. 執行 Gmsh
            generator = GmshGenerator()
            gmsh_result = generator.generate_from_mesh(
                vertices_blender, 
                faces,
                remesh_mode=remesh_mode,
                use_local_density=config.get_use_local_density(),
                bl_enabled=config.get_bl_enabled(),
                optimize=config.get_gmsh_optimize()
            )
            
            if not gmsh_result:
                self.report({'ERROR'}, "Gmsh 失敗")
                return {'CANCELLED'}
            
            # 6. 驗證網格
            validator = MeshValidator()
            if not validator.validate(gmsh_result['vertices'], gmsh_result['elements']):
                self.report({'WARNING'}, "四面體網格可能有問題")
            
            # 7. 創建線框視覺化
            wireframe_obj = self._create_wireframe_visualization(
                gmsh_result['vertices'], 
                gmsh_result['elements'],
                obj.name
            )
            
            # 8. 儲存到全域（使用線框物件名稱作為 key）
            wireframe_name = wireframe_obj.name
            config.object_tet_data[wireframe_name] = gmsh_result
            
            # 9. 初始化線框物件材質屬性
            config.simulation_config.initialize_object_material(wireframe_obj)
            
            # 10. 確保線框物件在 Collection 中
            collection = context.scene.warp_collection
            if collection is None:
                # 創建新 Collection
                collection = bpy.data.collections.new("WarpCollection")
                context.scene.collection.children.link(collection)
                context.scene.warp_collection = collection
                print("✅ 已創建 WarpCollection")
            
            # 將線框物件加入 Collection（而非原物件）
            if wireframe_name not in collection.objects:
                collection.objects.link(wireframe_obj)
                # 從場景 Collection 移除（避免重複）
                if wireframe_name in context.scene.collection.objects:
                    context.scene.collection.objects.unlink(wireframe_obj)
            
            # 9. 顯示統計資訊
            stats = gmsh_result['stats']
            print("\n📊 網格統計:")
            print(f"   四面體數: {stats['tet_count']:,}")
            print(f"   平均品質: {stats['avg_quality']:.4f}")
            print(f"   總體積: {stats['total_volume']:.6f}")
            
            print("=" * 60)
            print("✅ Gmsh 完成！")
            print("=" * 60 + "\n")
            
            self.report({'INFO'}, f"Gmsh 完成：{len(gmsh_result['elements'])} 四面體")
            return {'FINISHED'}
            
        except Exception as e:
            print(f"❌ Gmsh 失敗: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Gmsh 失敗: {str(e)}")
            return {'CANCELLED'}
        
        finally:
            # 清除臨時物件
            if temp_obj and temp_obj.name in bpy.data.objects:
                bpy.data.objects.remove(temp_obj, do_unlink=True)
    
    def _create_temp_copy(self, obj):
        """創建臨時副本"""
        temp_obj = obj.copy()
        temp_obj.data = obj.data.copy()
        temp_obj.name = obj.name + "_GmshTemp"
        bpy.context.collection.objects.link(temp_obj)
        
        # 設置為活動物件
        bpy.context.view_layer.objects.active = temp_obj
        temp_obj.select_set(True)
        obj.select_set(False)
        
        return temp_obj
    
    def _apply_remesh(self, obj, remesh_mode):
        """應用 Remesh 修改器"""
        mod = obj.modifiers.new(name="Remesh", type='REMESH')
        mod.mode = remesh_mode
        
        if remesh_mode in ['SMOOTH', 'SHARP']:
            mod.octree_depth = config.get_remesh_octree_depth()
            print(f"   Octree Depth: {mod.octree_depth}")
        elif remesh_mode == 'VOXEL':
            mod.voxel_size = config.get_remesh_voxel_size()
            print(f"   Voxel Size: {mod.voxel_size}")
        
        # 應用修改器
        with bpy.context.temp_override(active_object=obj, selected_objects=[obj]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        
        print(f"   ✅ Remesh 完成: {len(obj.data.vertices)} 頂點")
    
    def _triangulate(self, obj):
        """三角化網格"""
        with bpy.context.temp_override(active_object=obj, selected_objects=[obj]):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.object.mode_set(mode='OBJECT')
        
        print(f"   ✅ 三角化完成")
    
    def _extract_mesh_data(self, obj):
        """提取網格數據"""
        mesh = obj.data
        
        # 頂點（世界座標）
        vertices = np.array([
            obj.matrix_world @ v.co for v in mesh.vertices
        ], dtype=np.float32)
        
        # 三角形面
        faces = np.array([
            [p.vertices[0], p.vertices[1], p.vertices[2]]
            for p in mesh.polygons if len(p.vertices) == 3
        ], dtype=np.int32)
        
        return vertices, faces
    
    def _create_wireframe_visualization(self, vertices, elements, base_name):
        """創建四面體線框視覺化"""
        # 提取所有邊
        edges_set = set()
        edge_patterns = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
        
        for tet in elements:
            for i, j in edge_patterns:
                edge = tuple(sorted([tet[i], tet[j]]))
                edges_set.add(edge)
        
        edges = list(edges_set)
        
        # 創建網格
        mesh_name = f"{base_name}_GmshWire"
        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(vertices.tolist(), edges, [])
        mesh.update()
        
        # 創建物件
        obj = bpy.data.objects.new(mesh_name, mesh)
        bpy.context.collection.objects.link(obj)
        
        # 設置顯示
        obj.display_type = 'WIRE'
        obj.color = (1.0, 0.5, 0.0, 1.0)  # 橘色
        obj.hide_render = True
        
        # 儲存線框物件引用
        config.wireframe_objects[base_name] = obj
        
        print(f"✅ 線框視覺化: {mesh_name} ({len(edges)} 條邊)")

        return obj