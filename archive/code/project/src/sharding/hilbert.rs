// src/sharding/hilbert.rs
#[derive(Debug)]
pub struct HilbertCurve {
    dimensions: u32,
    order: u32,
}

impl HilbertCurve {
    pub fn new(dimensions: u32, order: u32) -> Self {
        Self { dimensions, order }
    }

    pub fn compute_index(&self, point: &[u32]) -> u64 {
        // Implementation of Hilbert curve index computation
        // This is a simplified version; real implementation would be more complex
        let mut index = 0u64;
        for (i, &p) in point.iter().enumerate() {
            index |= (p as u64) << (i * self.order as u64);
        }
        index
    }

    pub fn partition<T>(&self, data: &[(T, [u32; 2])]) -> Vec<Vec<T>> 
    where T: Clone {
        let mut indexed: Vec<_> = data.iter()
            .map(|(item, point)| (self.compute_index(point), item))
            .collect();
        
        indexed.sort_by_key(|(index, _)| *index);
        
        let chunk_size = (data.len() + self.dimensions as usize - 1) / self.dimensions as usize;
        indexed.chunks(chunk_size)
            .map(|chunk| chunk.iter().map(|(_, item)| (*item).clone()).collect())
            .collect()
    }
    
    // More advanced implementation of Hilbert curve indexing
    pub fn compute_index_advanced(&self, point: &[u32]) -> u64 {
        let n = 2u32.pow(self.order); // Number of points along each dimension
        
        if point.len() != 2 {
            return 0; // Only 2D implemented for simplicity
        }
        
        let mut x = point[0] % n;
        let mut y = point[1] % n;
        
        let mut d = 0u64;
        let mut s = n / 2;
        
        while s > 0 {
            let rx = (x & s) > 0;
            let ry = (y & s) > 0;
            
            d += s as u64 * s as u64 * ((3 * rx as u64) ^ ry as u64);
            
            // Rotate quadrant if needed
            if !ry {
                if rx {
                    x = n - 1 - x;
                    y = n - 1 - y;
                }
                
                // Swap x and y
                let t = x;
                x = y;
                y = t;
            }
            
            s /= 2;
        }
        
        d
    }
    
    pub fn find_nearest_neighbors<T>(&self, query_point: [u32; 2], data: &[(T, [u32; 2])], k: usize) -> Vec<&T>
    where T: Clone {
        let query_index = self.compute_index_advanced(&query_point);
        
        // Calculate distances (in Hilbert space)
        let mut distances: Vec<_> = data.iter()
            .map(|(item, point)| {
                let idx = self.compute_index_advanced(point);
                let distance = if idx > query_index {
                    idx - query_index
                } else {
                    query_index - idx
                };
                (distance, item)
            })
            .collect();
        
        // Sort by distance
        distances.sort_by_key(|(dist, _)| *dist);
        
        // Return k nearest
        distances.iter()
            .take(k)
            .map(|(_, item)| *item)
            .collect()
    }
}
