import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    build: {
        outDir: 'dist',
        emptyOutDir: true,
        rollupOptions: {
            input: {
                content: path.resolve(__dirname, 'src/main.js'),
            },
            output: {
                entryFileNames: '[name].js',
                chunkFileNames: '[name].js',
                assetFileNames: '[name].[ext]',
                // Ensure IIFE format if possible to wrap code, but standard ES module bundle is fine if we manually namespace in entry.
                // For extension content scripts, IIFE is safer to avoid collisions.
                format: 'iife',
                name: 'MTSunoPlugin' // Global variable name for IIFE
            }
        }
    },
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src')
        }
    }
})
