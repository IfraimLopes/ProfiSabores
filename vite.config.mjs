import { defineConfig } from 'vite';

export default defineConfig({
    build: {
        lib: {
            entry: 'static/src/capacitor.js',
            name: 'ProfisaboresCapacitor',
            formats: ['iife'],
            fileName: () => 'capacitor.js'
        },
        outDir: 'static/dist',
        emptyOutDir: true,
        minify: false
    }
});
