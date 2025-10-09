"""
網格驗證器 - 檢查四面體網格的有效性
"""

import numpy as np


class MeshValidator:
    """四面體網格驗證器"""
    
    def compute_tet_volumes(self, vertices, elements):
        """
        計算四面體體積（保留符號）
        
        Args:
            vertices: 頂點數組 (N, 3)
            elements: 四面體索引 (M, 4)
        
        Returns:
            volumes: 體積數組 (M,)
        """
        volumes = np.zeros(len(elements), dtype=np.float32)
        
        for i, tet in enumerate(elements):
            v0, v1, v2, v3 = vertices[tet]
            
            edge1 = v1 - v0
            edge2 = v2 - v0
            edge3 = v3 - v0
            
            volumes[i] = np.dot(edge1, np.cross(edge2, edge3)) / 6.0
        
        return volumes
    
    def validate(self, vertices, elements):
        """
        驗證四面體網格
        
        Returns:
            bool: 是否有效
        """
        # 檢查維度
        if vertices.ndim != 2 or vertices.shape[1] != 3:
            print(f"❌ 頂點維度錯誤: {vertices.shape}")
            return False
        
        if elements.ndim != 2 or elements.shape[1] != 4:
            print(f"❌ 四面體維度錯誤: {elements.shape}")
            return False
        
        # 檢查索引範圍
        max_index = np.max(elements)
        if max_index >= len(vertices):
            print(f"❌ 索引超出範圍: {max_index} >= {len(vertices)}")
            return False
        
        # 檢查體積
        volumes = self.compute_tet_volumes(vertices, elements)
        invalid_count = np.sum(volumes <= 0)
        
        if invalid_count > 0:
            print(f"⚠️ {invalid_count} 個反轉四面體")
            return False
        
        print(f"✅ 網格驗證通過")
        print(f"   頂點: {len(vertices)}")
        print(f"   四面體: {len(elements)}")
        print(f"   體積範圍: {np.min(volumes):.6f} ~ {np.max(volumes):.6f}")
        
        return True