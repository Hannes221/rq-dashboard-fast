import { defineConfig, presetWind } from 'unocss'
import presetWebFonts from '@unocss/preset-web-fonts'
import { createLocalFontProcessor } from '@unocss/preset-web-fonts/local'

export default defineConfig({
  presets: [
    presetWind(),
    presetWebFonts({
      provider: 'google',
      fonts: {
        sans: 'Inter:300,400,500,600,700',
      },
      processors: createLocalFontProcessor({
        cacheDir: 'node_modules/.cache/unocss/fonts',
        fontAssetsDir: 'rq_dashboard_fast/static/fonts',
        fontServeBaseUrl: '../fonts',
      }),
    }),
  ],
  darkMode: 'class',
  safelist: [
    'badge-failed', 'badge-started', 'badge-queued',
    'badge-finished', 'badge-deferred', 'badge-scheduled',
    // Pagination (dynamically generated in JS)
    'opacity-40', 'cursor-not-allowed', 'min-w-9', 'h-9',
    'bg-blue-600', 'dark:bg-blue-500', 'cursor-default',
    'select-none',
  ],
  shortcuts: {
    'btn': 'px-3 py-1.5 rounded-md cursor-pointer border-none text-sm font-medium transition-colors duration-150',
    'btn-icon': 'inline-flex items-center justify-center w-8 h-8 rounded-md cursor-pointer border-none transition-colors duration-150',
    'btn-delete': 'btn-icon bg-red-50 text-red-500 hover:bg-red-100 hover:text-red-700 dark:bg-red-950/40 dark:text-red-400 dark:hover:bg-red-900/60 dark:hover:text-red-300',
    'btn-requeue': 'btn-icon bg-blue-50 text-blue-500 hover:bg-blue-100 hover:text-blue-700 dark:bg-blue-950/40 dark:text-blue-400 dark:hover:bg-blue-900/60 dark:hover:text-blue-300',
    'btn-pagination': 'btn-icon bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200',
    'btn-back': 'btn px-4 py-2 bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 no-underline',
    'btn-export': 'btn px-4 py-2 bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700',
    'data-table': 'w-full mt-5 text-sm',
    'th-cell': 'px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 border-b-2 border-gray-300 dark:border-gray-600',
    'td-cell': 'px-4 py-3 text-left text-gray-900 dark:text-gray-200 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 align-middle',
    'tr-stripe': 'hover:bg-gray-50 dark:hover:bg-gray-800/50',
    'badge': 'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide',
    'badge-failed': 'badge bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300',
    'badge-started': 'badge bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
    'badge-queued': 'badge bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300',
    'badge-finished': 'badge bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300',
    'badge-deferred': 'badge bg-gray-100 text-gray-700 dark:bg-gray-600/30 dark:text-gray-300',
    'badge-scheduled': 'badge bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300',
  },
})
