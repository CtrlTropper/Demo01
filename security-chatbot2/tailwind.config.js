// /** @type {import('tailwindcss').Config} */
// export default {
//   content: [
//     "./index.html",
//     "./src/**/*.{js,ts,jsx,tsx}",
//   ],
//   theme: {
//     extend: {
//       colors: {
//         'primary-blue': '#3b82f6',
//         'dark-slate': '#1e293b',
//         'success-green': '#22c55e',
//         'warning-yellow': '#f59e0b',
//         'danger-red': '#ef4444',
//         'neon-cyan': '#00ffff',
//         'matrix-green': '#00ff00',
//         'purple': '#8b5cf6',
//         'orange': '#f97316',
//       },
//       backgroundImage: {
//         'security-gradient': 'linear-gradient(to right, #3b82f6, #1e293b)',
//         'cyber-glow': 'linear-gradient(to bottom, #00ffff, #00ff00)',
//         'message-gradient': 'linear-gradient(to bottom right, #1e293b, #3b82f6)',
//       },
//       animation: {
//         glow: 'glow 1.5s ease-in-out infinite alternate',
//         typing: 'typing 1s steps(40, end) infinite',
//         'slide-up': 'slide-up 0.5s ease-out forwards',
//       },
//       keyframes: {
//         glow: {
//           '0%': { boxShadow: '0 0 5px #00ffff' },
//           '100%': { boxShadow: '0 0 20px #00ffff' },
//         },
//         typing: {
//           '0%': { width: '0' },
//           '100%': { width: '100%' },
//         },
//         'slide-up': {
//           '0%': { opacity: '0', transform: 'translateY(20px)' },
//           '100%': { opacity: '1', transform: 'translateY(0)' },
//         },
//       },
//     },
//   },
//   plugins: [
//     function ({ addUtilities }) {
//       addUtilities({
//         '.glass-effect': {
//           'backdrop-filter': 'blur(10px)',
//           'background-color': 'rgba(30, 41, 59, 0.5)', // Based on dark-slate with opacity
//           'border': '1px solid rgba(255, 255, 255, 0.1)',
//         },
//         '.security-border': {
//           'border': '2px solid #3b82f6',
//           'border-radius': '8px',
//         },
//         '.message-bubble': {
//           'border-radius': '20px',
//           'padding': '12px 16px',
//           'max-width': '75%',
//         },
//         '.cyber-grid': {
//           'background-image': 'linear-gradient(#00ffff 1px, transparent 1px), linear-gradient(to right, #00ffff 1px, transparent 1px)',
//           'background-size': '20px 20px',
//         },
//       });
//     },
//   ],
// }
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary-blue': '#3b82f6',
        'dark-slate': '#1e293b',
        'success-green': '#22c55e',
        'warning-yellow': '#f59e0b',
        'danger-red': '#ef4444',
        'neon-cyan': '#00ffff',
        'matrix-green': '#00ff00',
        'purple': '#8b5cf6',
        'orange': '#f97316',
      },
      backgroundImage: {
        'security-gradient': 'linear-gradient(to right, #3b82f6, #1e293b)',
        'cyber-glow': 'linear-gradient(to bottom, #00ffff, #00ff00)',
        'message-gradient': 'linear-gradient(to bottom right, #1e293b, #3b82f6)',
        'login-gradient': 'linear-gradient(to bottom right, #1e293b, #3b82f6)',
      },
      animation: {
        glow: 'glow 1.5s ease-in-out infinite alternate',
        typing: 'typing 1s steps(40, end) infinite',
        'slide-up': 'slide-up 0.5s ease-out forwards',
        'fade-in': 'fade-in 0.5s ease-out forwards',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #00ffff' },
          '100%': { boxShadow: '0 0 20px #00ffff' },
        },
        typing: {
          '0%': { width: '0' },
          '100%': { width: '100%' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [
    function ({ addUtilities }) {
      addUtilities({
        '.glass-effect': {
          'backdrop-filter': 'blur(10px)',
          'background-color': 'rgba(30, 41, 59, 0.5)',
          'border': '1px solid rgba(255, 255, 255, 0.1)',
        },
        '.security-border': {
          'border': '2px solid #3b82f6',
          'border-radius': '8px',
        },
        '.message-bubble': {
          'border-radius': '20px',
          'padding': '12px 16px',
          'max-width': '75%',
        },
        '.cyber-grid': {
          'background-image': 'linear-gradient(#00ffff 1px, transparent 1px), linear-gradient(to right, #00ffff 1px, transparent 1px)',
          'background-size': '20px 20px',
        },
      });
    },
  ],
}