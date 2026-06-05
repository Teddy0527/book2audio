/** @type {import('tailwindcss').Config} */
// CSSの再ビルド方法:
//   cd book2audio
//   npx tailwindcss@3 -c tailwind.config.js -i src.css -o book2audio/web/static/app.css --minify
// クラスを増減したら上記を再実行し、index.html の app.css?v= を上げてキャッシュ破棄する。
module.exports = {
  content: ["./book2audio/web/static/index.html"],
  theme: {
    extend: {
      colors: {
        bg: '#0A0A0A',
        surface: '#141414',
        surfaceHover: '#1A1A1A',
        border: '#262626',
        borderLight: '#333333',
        cta: '#D4AF37',
        ctaHover: '#E8C84A',
        ctaDim: 'rgba(212,175,55,0.15)',
        textPrimary: '#F5F5F5',
        textSecondary: '#A3A3A3',
        textMuted: '#6B6B6B',
        success: '#22C55E',
        error: '#EF4444',
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', '"Hiragino Kaku Gothic ProN"', '"Hiragino Sans"', '"Noto Sans JP"', 'Meiryo', 'sans-serif'],
        serif: ['"Hiragino Mincho ProN"', '"Yu Mincho"', 'YuMincho', '"Noto Serif JP"', 'serif'],
      },
    },
  },
  plugins: [],
}
