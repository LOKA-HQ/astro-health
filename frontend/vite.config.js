import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Split the heavy dependencies into their own chunks so the main bundle
// stays small: three.js (3D body model) and recharts (charts) load on demand.
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/three')) return 'three';
          if (id.includes('node_modules/recharts')) return 'charts';
          if (
            id.includes('node_modules/react') ||
            id.includes('node_modules/react-dom') ||
            id.includes('node_modules/lucide-react')
          ) {
            return 'vendor';
          }
          return undefined;
        },
      },
    },
  },
});
