"""
Gmsh 生成器 - 將 Blender 網格轉換為四面體
整合局部密度分析、邊界層控制、Remesh 等進階功能
"""

import numpy as np
from .. import config


class GmshGenerator:
    """Gmsh 四面體生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.gmsh_available = self._check_gmsh()
        self.scipy_available = self._check_scipy()
    
    def _check_gmsh(self):
        """檢查 Gmsh 是否可用"""
        try:
            import gmsh
            print(f"✅ Gmsh 版本: {gmsh.__version__}")
            return True
        except ImportError:
            print("❌ Gmsh 未安裝")
            print("   請執行: pip install gmsh")
            return False
    
    def _check_scipy(self):
        """檢查 SciPy 是否可用（局部密度需要）"""
        try:
            from scipy.spatial import KDTree
            print(f"✅ SciPy 可用（支援局部密度分析）")
            return True
        except ImportError:
            print("⚠️ SciPy 未安裝（局部密度功能不可用）")
            return False
    
    def generate_from_mesh(self, vertices_blender, faces, 
                          remesh_mode=None, use_local_density=None,
                          bl_enabled=None, optimize=None):
        """
        從表面網格生成四面體
        
        Args:
            vertices_blender: Blender 座標系的頂點 (N, 3)
            faces: 三角形面索引 (M, 3)
            remesh_mode: Remesh 模式（已在外部處理）
            use_local_density: 是否使用局部密度
            bl_enabled: 是否啟用邊界層
            optimize: 是否優化網格
            
        Returns:
            dict: {'vertices': array, 'elements': array, 'stats': dict} 或 None
        """
        if not self.gmsh_available:
            print("❌ Gmsh 不可用")
            return None
        
        import gmsh
        
        # 使用配置或預設值
        use_local_density = use_local_density if use_local_density is not None else config.get_use_local_density()
        bl_enabled = bl_enabled if bl_enabled is not None else config.get_bl_enabled()
        optimize = optimize if optimize is not None else config.get_gmsh_optimize()
        
        print(f"\n🚀 執行 Gmsh")
        print(f"   輸入頂點: {len(vertices_blender)}")
        print(f"   輸入面: {len(faces)}")
        print(f"   局部密度: {'啟用' if use_local_density else '全域平均'}")
        print(f"   邊界層: {'啟用' if bl_enabled else '關閉'}")
        print(f"   優化: {'啟用' if optimize else '關閉'}")
        
        try:
            # 初始化 Gmsh
            gmsh.initialize()
            if not config.get_gmsh_verbose():
                gmsh.option.setNumber("General.Terminal", 0)
            gmsh.model.add("BlenderMesh")
            
            # 1. 創建離散表面
            print(f"\n🔧 創建離散實體...")
            surface_tag, node_tags = self._create_discrete_surface(
                gmsh, vertices_blender, faces
            )
            
            # 2. 分析密度
            print(f"\n🔬 分析密度...")
            density_stats, actual_use_local = self._analyze_density_smart(
                vertices_blender, faces, use_local_density
            )
            
            # 3. 設置網格尺寸
            print(f"\n🎨 設置網格尺寸...")
            if actual_use_local:
                self._set_local_mesh_sizes(gmsh, node_tags, density_stats['vertex_sizes'])
            else:
                self._set_uniform_mesh_size(gmsh, node_tags, density_stats['avg_size'])
            
            # 4. 設置邊界層（如果啟用）
            if bl_enabled:
                bl_size = density_stats['avg_size'] * config.get_bl_size_multiplier()
                core_size = density_stats['avg_size'] * config.get_core_size_multiplier()
                print(f"\n🌊 設置邊界層...")
                print(f"   邊界層尺寸: {bl_size:.4f}")
                print(f"   核心尺寸: {core_size:.4f}")
                self._setup_boundary_layer_field(gmsh, surface_tag, bl_size, core_size)
            else:
                core_size = density_stats['avg_size'] * config.get_core_size_multiplier()
                gmsh.option.setNumber("Mesh.CharacteristicLengthMax", core_size)
            
            # 5. 生成體積網格
            print(f"\n🔧 生成體積網格...")
            algorithm = config.get_algorithm_3d()
            gmsh.option.setNumber("Mesh.Algorithm3D", algorithm)
            gmsh.model.mesh.generate(3)
            
            # 6. 優化（如果啟用）
            if optimize:
                print(f"\n⚡ 優化網格...")
                iterations = config.get_optimize_iterations()
                for i in range(iterations):
                    gmsh.model.mesh.optimize("Netgen")
                    if (i + 1) % 3 == 0:
                        print(f"   完成 {i+1}/{iterations} 次迭代")
            
            # 7. 提取四面體
            print(f"\n📊 提取四面體...")
            tet_vertices, tets = self._extract_tetrahedra(gmsh)
            
            if tet_vertices is None:
                return None
            
            # 8. 統計
            stats = self._calculate_statistics(tet_vertices, tets)
            stats['density_analysis'] = density_stats
            stats['used_local_density'] = actual_use_local
            stats['boundary_layer_enabled'] = bl_enabled
            
            print(f"\n✅ Gmsh 完成！")
            print(f"   輸出頂點: {len(tet_vertices)}")
            print(f"   輸出四面體: {len(tets)}")
            print(f"   平均品質: {stats['avg_quality']:.4f}")
            
            # 9. 修正反轉四面體
            tet_vertices, tets = self._fix_inverted_tets(tet_vertices, tets)
            
            return {
                'vertices': tet_vertices,
                'elements': tets,
                'stats': stats
            }
            
        except Exception as e:
            print(f"❌ Gmsh 失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            gmsh.finalize()
    
    # ============================================================
    # 密度分析
    # ============================================================
    
    def _analyze_density_smart(self, vertices, faces, use_local_requested):
        """智能選擇密度分析方法"""
        
        # 如果用戶要求局部密度但 SciPy 不可用，降級為全域
        if use_local_requested and not self.scipy_available:
            print(f"  ⚠️ SciPy 不可用，使用全域密度")
            use_local_requested = False
        
        if use_local_requested:
            print(f"  🔬 使用局部密度分析")
            density_stats = self._analyze_local_density_with_blur(vertices, faces)
            return density_stats, True
        else:
            print(f"  📊 使用全域平均")
            density_stats = self._analyze_global_density(vertices, faces)
            return density_stats, False
    
    def _analyze_global_density(self, vertices, faces):
        """全域平均密度"""
        edge_lengths = []
        
        for tri in faces:
            v0, v1, v2 = vertices[tri]
            edge_lengths.append(np.linalg.norm(v1 - v0))
            edge_lengths.append(np.linalg.norm(v2 - v1))
            edge_lengths.append(np.linalg.norm(v0 - v2))
        
        edge_lengths = np.array(edge_lengths)
        
        return {
            'vertex_sizes': None,
            'avg_size': float(edge_lengths.mean()),
            'min_size': float(edge_lengths.min()),
            'max_size': float(edge_lengths.max()),
            'median_size': float(np.median(edge_lengths)),
            'std_size': float(edge_lengths.std()),
        }
    
    def _analyze_local_density_with_blur(self, vertices, faces):
        """局部密度分析 + 高斯模糊"""
        from scipy.spatial import KDTree
        
        # 1. 計算每個頂點的局部邊長
        print(f"    計算局部邊長...")
        vertex_edge_lengths = [[] for _ in range(len(vertices))]
        
        for tri in faces:
            v0, v1, v2 = vertices[tri]
            e0 = np.linalg.norm(v1 - v0)
            e1 = np.linalg.norm(v2 - v1)
            e2 = np.linalg.norm(v0 - v2)
            
            vertex_edge_lengths[tri[0]].extend([e0, e2])
            vertex_edge_lengths[tri[1]].extend([e0, e1])
            vertex_edge_lengths[tri[2]].extend([e1, e2])
        
        local_sizes = np.array([np.mean(edges) if edges else 0.1 
                                for edges in vertex_edge_lengths])
        
        # 2. 去除異常值（如果啟用）
        if config.get_outlier_removal():
            print(f"    去除異常值...")
            q1, q3 = np.percentile(local_sizes, [25, 75])
            iqr = q3 - q1
            lower_bound = max(q1 - 1.5 * iqr, local_sizes.min())
            upper_bound = min(q3 + 1.5 * iqr, local_sizes.max())
            local_sizes = np.clip(local_sizes, lower_bound, upper_bound)
        
        # 3. 高斯模糊
        blur_radius = config.get_blur_radius()
        print(f"    高斯模糊 (radius={blur_radius})...")
        smoothed_sizes = self._gaussian_blur_sizes(vertices, local_sizes, blur_radius)
        
        # 4. 限制範圍
        avg_size = smoothed_sizes.mean()
        size_clamp = config.get_size_clamp_ratio()
        min_allowed = avg_size / size_clamp
        max_allowed = avg_size * size_clamp
        smoothed_sizes = np.clip(smoothed_sizes, min_allowed, max_allowed)
        
        return {
            'vertex_sizes': smoothed_sizes,
            'avg_size': float(smoothed_sizes.mean()),
            'min_size': float(smoothed_sizes.min()),
            'max_size': float(smoothed_sizes.max()),
            'median_size': float(np.median(smoothed_sizes)),
            'std_size': float(smoothed_sizes.std()),
            'size_range_ratio': float(smoothed_sizes.max() / smoothed_sizes.min()),
        }
    
    def _gaussian_blur_sizes(self, vertices, local_sizes, blur_radius):
        """高斯模糊頂點尺寸"""
        from scipy.spatial import KDTree
        
        tree = KDTree(vertices)
        smoothed_sizes = np.zeros(len(vertices))
        k = blur_radius * 5
        
        for i, vertex in enumerate(vertices):
            distances, indices = tree.query(vertex, k=min(k, len(vertices)))
            
            if len(indices) < 2:
                smoothed_sizes[i] = local_sizes[i]
                continue
            
            sigma = np.median(distances[1:])
            
            if sigma < 1e-10:
                smoothed_sizes[i] = local_sizes[i]
                continue
            
            weights = np.exp(-(distances**2) / (2 * sigma**2))
            weights /= weights.sum()
            
            smoothed_sizes[i] = np.sum(local_sizes[indices] * weights)
        
        return smoothed_sizes
    
    # ============================================================
    # Gmsh 操作
    # ============================================================
    
    def _create_discrete_surface(self, gmsh, vertices, faces):
        """創建 Gmsh 離散表面"""
        surface_tag = gmsh.model.addDiscreteEntity(2)
        
        node_tags = list(range(1, len(vertices) + 1))
        coords = vertices.flatten().tolist()
        gmsh.model.mesh.addNodes(2, surface_tag, node_tags, coords)
        
        element_tags = list(range(1, len(faces) + 1))
        node_tags_flat = (faces + 1).flatten().tolist()
        gmsh.model.mesh.addElementsByType(surface_tag, 2, element_tags, node_tags_flat)
        
        surface_loop = gmsh.model.geo.addSurfaceLoop([surface_tag])
        volume_tag = gmsh.model.geo.addVolume([surface_loop])
        gmsh.model.geo.synchronize()
        
        return surface_tag, node_tags
    
    def _set_local_mesh_sizes(self, gmsh, node_tags, vertex_sizes):
        """設置局部網格尺寸"""
        for i, node_tag in enumerate(node_tags):
            gmsh.model.mesh.setSize([(0, node_tag)], vertex_sizes[i])
        print(f"    已設置 {len(node_tags)} 個局部尺寸")
    
    def _set_uniform_mesh_size(self, gmsh, node_tags, size):
        """設置統一網格尺寸"""
        for node_tag in node_tags:
            gmsh.model.mesh.setSize([(0, node_tag)], size)
        print(f"    已設置統一尺寸: {size:.4f}")
    
    def _setup_boundary_layer_field(self, gmsh, surface_tag, bl_size, core_size):
        """設置邊界層尺寸場"""
        bl_thickness = config.get_bl_thickness()
        
        distance_field = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(distance_field, "SurfacesList", [surface_tag])
        gmsh.model.mesh.field.setNumber(distance_field, "Sampling", 100)
        
        threshold_field = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
        gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", bl_size)
        gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", core_size)
        gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", bl_thickness)
        gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", bl_thickness * 1.5)
        
        gmsh.model.mesh.field.setAsBackgroundMesh(threshold_field)
        
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        
        print(f"    邊界層: 0~{bl_thickness} ({bl_size:.4f} → {core_size:.4f})")
    
    def _extract_tetrahedra(self, gmsh):
        """提取四面體數據"""
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        vertices = node_coords.reshape(-1, 3)
        
        node_map = {tag: idx for idx, tag in enumerate(node_tags)}
        
        element_types, element_tags, element_node_tags = gmsh.model.mesh.getElements(3)
        
        if len(element_types) == 0:
            print("❌ 未找到四面體")
            return None, None
        
        tets_raw = element_node_tags[0].reshape(-1, 4)
        tets = np.array([[node_map[tag] for tag in tet] for tet in tets_raw])
        
        return vertices, tets
    
    def _calculate_statistics(self, vertices, tets):
        """計算統計"""
        volumes = []
        qualities = []
        
        for tet in tets:
            v0, v1, v2, v3 = vertices[tet]
            
            vol = abs(np.dot(v1-v0, np.cross(v2-v0, v3-v0))) / 6.0
            volumes.append(vol)
            
            edges = [v1-v0, v2-v0, v3-v0, v2-v1, v3-v1, v3-v2]
            edge_lengths = [np.linalg.norm(e) for e in edges]
            
            if vol > 1e-10:
                sum_edge_sq = sum(l**2 for l in edge_lengths)
                quality = 12.0 * (3.0 * vol)**(2.0/3.0) / sum_edge_sq
            else:
                quality = 0.0
            
            qualities.append(quality)
        
        volumes = np.array(volumes)
        qualities = np.array(qualities)
        
        return {
            'vertex_count': len(vertices),
            'tet_count': len(tets),
            'total_volume': float(volumes.sum()),
            'avg_volume': float(volumes.mean()),
            'min_volume': float(volumes.min()),
            'max_volume': float(volumes.max()),
            'avg_quality': float(qualities.mean()),
            'min_quality': float(qualities.min()),
        }
    
    # ============================================================
    # 四面體修正
    # ============================================================
    
    def _fix_inverted_tets(self, vertices, elements, max_attempts=10):
        """修正反轉四面體"""
        from .mesh_validator import MeshValidator
        
        validator = MeshValidator()
        
        for attempt in range(max_attempts):
            volumes = validator.compute_tet_volumes(vertices, elements)
            invalid_indices = np.where(volumes <= 0)[0]
            
            if len(invalid_indices) == 0:
                break
            
            print(f"⚠️ 嘗試 {attempt+1}/{max_attempts}: 修正 {len(invalid_indices)} 個反轉四面體")
            
            # 如果全部反轉，交換索引 0-1
            if len(invalid_indices) == len(elements):
                print("   → 全部反轉，交換索引 0-1")
                elements = elements[:, [1, 0, 2, 3]]
            else:
                # 個別修正
                permutation_strategy = attempt % 6
                elements = self._permute_tet_indices(elements, invalid_indices, permutation_strategy)
        
        # 最終檢查
        volumes = validator.compute_tet_volumes(vertices, elements)
        invalid_count = np.sum(volumes <= 0)
        
        if invalid_count > 0:
            print(f"⚠️ 仍有 {invalid_count} 個反轉四面體")
        else:
            print(f"✅ 所有四面體方向正確")
        
        return vertices, elements
    
    def _permute_tet_indices(self, elements, invalid_indices, strategy):
        """排列四面體索引以修正反轉"""
        elements = elements.copy()
        
        permutations = [
            [0, 1, 2, 3],  # 原始
            [1, 0, 2, 3],  # 交換 0-1
            [0, 2, 1, 3],  # 交換 1-2
            [0, 1, 3, 2],  # 交換 2-3
            [2, 1, 0, 3],  # 交換 0-2
            [1, 2, 0, 3]   # 循環
        ]
        
        perm = permutations[strategy]
        
        for idx in invalid_indices:
            elements[idx] = elements[idx, perm]
        
        return elements