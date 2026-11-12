/*
File Name: mathSymbols.js
Description: Shared formula symbol table (math, physics, chemistry, greek) used by the teacher question editor and the student answer editor toolbars.
Created At: 2026-11-12
Created By: AI Agent
Updated At: 2026-11-12
Updated By: AI Agent
*/

export const symbolCategoriesBySubject = {
  math: {
    name: 'Toán học',
    icon: '📐',
    groups: [
      {
        group: 'Đại số:',
        items: [
          { label: '\\frac{a}{b}', code: '\\frac{a}{b}', tpl: '\\frac{#?}{#?}', display: '\\frac{a}{b}', tip: 'Phân số a/b' },
          { label: 'x^n', code: 'x^{n}', tpl: '#@^{#?}', display: 'x^{n}', tip: 'Lũy thừa x^n' },
          { label: 'x_k', code: 'x_{k}', tpl: '#@_{#?}', display: 'x_{k}', tip: 'Chỉ số dưới x_k' },
          { label: '\\sqrt{x}', code: '\\sqrt{x}', tpl: '\\sqrt{#?}', display: '\\sqrt{x}', tip: 'Căn bậc 2' },
          { label: '\\sqrt[n]{x}', code: '\\sqrt[n]{x}', tpl: '\\sqrt[#?]{#?}', display: '\\sqrt[n]{x}', tip: 'Căn bậc n' },
          { label: '|x|', code: '|x|', tpl: '\\left\\lvert #? \\right\\rvert', display: '|x|', tip: 'Giá trị tuyệt đối' },
          { label: '\\pm', code: '\\pm', display: '\\pm', tip: 'Cộng trừ' },
          { label: '\\times', code: '\\times', display: '\\times', tip: 'Phép nhân' },
          { label: '\\div', code: '\\div', display: '\\div', tip: 'Phép chia' },
          { label: '\\log_a b', code: '\\log_{a} b', tpl: '\\log_{#?}{#?}', display: '\\log_{a} b', tip: 'Logarit cơ số a của b' },
          { label: '\\ln x', code: '\\ln x', display: '\\ln x', tip: 'Logarit tự nhiên' }
        ]
      },
      {
        group: 'Giải tích:',
        items: [
          { label: '\\int_{a}^{b}', code: '\\int_{a}^{b} f(x)\\,dx', tpl: '\\int_{#?}^{#?} #? \\,dx', display: '\\int_{a}^{b}', tip: 'Tích phân xác định' },
          { label: '\\int', code: '\\int f(x)\\,dx', tpl: '\\int #? \\,dx', display: '\\int', tip: 'Nguyên hàm' },
          { label: '\\frac{dy}{dx}', code: '\\frac{dy}{dx}', display: '\\frac{dy}{dx}', tip: 'Đạo hàm dy/dx' },
          { label: "f'(x)", code: "f'(x)", display: "f'(x)", tip: 'Đạo hàm f(x)' },
          { label: '\\sum_{i=1}^{n}', code: '\\sum_{i=1}^{n}', tpl: '\\sum_{#?}^{#?}', display: '\\sum_{i=1}^{n}', tip: 'Tổng sigma' },
          { label: '\\lim_{x \\to x_0}', code: '\\lim_{x \\to x_0}', tpl: '\\lim_{#? \\to #?}', display: '\\lim_{x \\to x_0}', tip: 'Giới hạn lim' },
          { label: '\\infty', code: '\\infty', display: '\\infty', tip: 'Vô cực' }
        ]
      },
      {
        group: 'Hình học:',
        items: [
          { label: '\\vec{u}', code: '\\vec{u}', tpl: '\\vec{#?}', display: '\\vec{u}', tip: 'Véc-tơ u' },
          { label: '\\overrightarrow{AB}', code: '\\overrightarrow{AB}', tpl: '\\overrightarrow{#?}', display: '\\overrightarrow{AB}', tip: 'Véc-tơ AB' },
          { label: '\\widehat{ABC}', code: '\\widehat{ABC}', tpl: '\\widehat{#?}', display: '\\widehat{ABC}', tip: 'Góc ABC' },
          { label: '\\perp', code: '\\perp', display: '\\perp', tip: 'Vuông góc' },
          { label: '\\parallel', code: '\\parallel', display: '\\parallel', tip: 'Song song' },
          { label: '\\Delta', code: '\\Delta', display: '\\Delta', tip: 'Tam giác / Delta' },
          { label: '\\angle', code: '\\angle', display: '\\angle', tip: 'Ký hiệu góc' },
          { label: '^{\\circ}', code: '^{\\circ}', display: '^{\\circ}', tip: 'Độ' }
        ]
      },
      {
        group: 'Tập hợp & Quan hệ:',
        items: [
          { label: '\\in', code: '\\in', display: '\\in', tip: 'Thuộc' },
          { label: '\\notin', code: '\\notin', display: '\\notin', tip: 'Không thuộc' },
          { label: '\\subset', code: '\\subset', display: '\\subset', tip: 'Tập con' },
          { label: '\\cup', code: '\\cup', display: '\\cup', tip: 'Hợp' },
          { label: '\\cap', code: '\\cap', display: '\\cap', tip: 'Giao' },
          { label: '\\setminus', code: '\\setminus', display: '\\setminus', tip: 'Hiệu' },
          { label: '\\emptyset', code: '\\emptyset', display: '\\emptyset', tip: 'Tập rỗng' },
          { label: '\\le', code: '\\le', display: '\\le', tip: 'Nhỏ hơn hoặc bằng' },
          { label: '\\ge', code: '\\ge', display: '\\ge', tip: 'Lớn hơn hoặc bằng' },
          { label: '\\neq', code: '\\neq', display: '\\neq', tip: 'Khác' },
          { label: '\\approx', code: '\\approx', display: '\\approx', tip: 'Xấp xỉ' },
          { label: '\\Rightarrow', code: '\\Rightarrow', display: '\\Rightarrow', tip: 'Suy ra' },
          { label: '\\Leftrightarrow', code: '\\Leftrightarrow', display: '\\Leftrightarrow', tip: 'Tương đương' }
        ]
      }
    ]
  },
  physics: {
    name: 'Vật lí',
    icon: '⚡',
    groups: [
      {
        group: 'Cơ học & Nhiệt:',
        items: [
          { label: '\\vec{F}', code: '\\vec{F}', display: '\\vec{F}', tip: 'Véc-tơ lực F' },
          { label: '\\vec{v}', code: '\\vec{v}', display: '\\vec{v}', tip: 'Véc-tơ vận tốc v' },
          { label: '\\vec{a}', code: '\\vec{a}', display: '\\vec{a}', tip: 'Véc-tơ gia tốc a' },
          { label: '\\Delta t', code: '\\Delta t', display: '\\Delta t', tip: 'Thời gian Delta t' },
          { label: '\\vec{p}', code: '\\vec{p}', display: '\\vec{p}', tip: 'Động lượng' },
          { label: 'E_d', code: 'E_d = \\frac{1}{2}mv^2', display: 'E_d', tip: 'Động năng' },
          { label: 'E_t', code: 'E_t = mgh', display: 'E_t', tip: 'Thế năng' },
          { label: 'W', code: 'W = F \\cdot s \\cdot \\cos\\alpha', display: 'W', tip: 'Công cơ học' },
          { label: '\\mu', code: '\\mu', display: '\\mu', tip: 'Hệ số ma sát' },
          { label: '\\rho', code: '\\rho', display: '\\rho', tip: 'Khối lượng riêng' },
          { label: 'T(K)', code: 'T\\text{ (K)}', display: 'T\\text{ (K)}', tip: 'Nhiệt độ Kelvin' },
          { label: '^{\\circ}C', code: '^{\\circ}\\text{C}', display: '^{\\circ}\\text{C}', tip: 'Độ C' },
          { label: 'Q', code: 'Q = mc\\Delta t', display: 'Q', tip: 'Nhiệt lượng' }
        ]
      },
      {
        group: 'Điện - Từ & Sóng:',
        items: [
          { label: '\\lambda', code: '\\lambda', display: '\\lambda', tip: 'Bước sóng lambda' },
          { label: '\\omega', code: '\\omega', display: '\\omega', tip: 'Tần số góc omega' },
          { label: '\\Omega', code: '\\Omega', display: '\\Omega', tip: 'Điện trở Ôm (Ohm)' },
          { label: '\\mu F', code: '\\mu\\text{F}', display: '\\mu\\text{F}', tip: 'Microfarad' },
          { label: 'mH', code: '\\text{mH}', display: '\\text{mH}', tip: 'Milihenry' },
          { label: '\\vec{E}', code: '\\vec{E}', display: '\\vec{E}', tip: 'Điện trường' },
          { label: '\\vec{B}', code: '\\vec{B}', display: '\\vec{B}', tip: 'Từ trường' },
          { label: '\\Phi', code: '\\Phi', display: '\\Phi', tip: 'Từ thông' },
          { label: '\\mathcal{E}', code: '\\mathcal{E}', display: '\\mathcal{E}', tip: 'Suất điện động' },
          { label: 'I=U/R', code: 'I = \\frac{U}{R}', display: 'I=\\frac{U}{R}', tip: 'Định luật Ôm' },
          { label: 'P=UI', code: 'P = U \\cdot I', display: 'P=UI', tip: 'Công suất điện' }
        ]
      },
      {
        group: 'Lượng tử & Hạt nhân:',
        items: [
          { label: 'h\\nu', code: '\\varepsilon = h\\nu', display: 'h\\nu', tip: 'Lượng tử năng lượng' },
          { label: 'E=mc^2', code: 'E = mc^2', display: 'E=mc^2', tip: 'Hệ thức Einstein' },
          { label: '_{Z}^{A}X', code: '_{Z}^{A}\\text{X}', display: '_{Z}^{A}\\text{X}', tip: 'Ký hiệu hạt nhân' },
          { label: '_{2}^{4}He', code: '_{2}^{4}\\text{He}', display: '_{2}^{4}\\text{He}', tip: 'Hạt alpha' },
          { label: '_{-1}^{0}e', code: '_{-1}^{0}\\text{e}', display: '_{-1}^{0}\\text{e}', tip: 'Hạt beta' },
          { label: '\\gamma', code: '\\gamma', display: '\\gamma', tip: 'Tia gamma' },
          { label: 'T_{1/2}', code: 'T_{1/2}', display: 'T_{1/2}', tip: 'Chu kỳ bán rã' }
        ]
      }
    ]
  },
  chemistry: {
    name: 'Hóa học',
    icon: '🧪',
    groups: [
      {
        group: 'Mũi tên & Điều kiện:',
        items: [
          { label: '\\rightarrow', code: '\\rightarrow', display: '\\rightarrow', tip: 'Phản ứng một chiều' },
          { label: '\\rightleftharpoons', code: '\\rightleftharpoons', display: '\\rightleftharpoons', tip: 'Phản ứng thuận nghịch' },
          { label: '\\uparrow', code: '\\uparrow', display: '\\uparrow', tip: 'Khí thoát ra' },
          { label: '\\downarrow', code: '\\downarrow', display: '\\downarrow', tip: 'Kết tủa' },
          { label: '\\xrightarrow{t^{\\circ}}', code: '\\xrightarrow{t^{\\circ}}', display: '\\xrightarrow{t^{\\circ}}', tip: 'Nhiệt độ' },
          { label: '\\xrightarrow{\\text{xt}}', code: '\\xrightarrow{\\text{xt}}', display: '\\xrightarrow{\\text{xt}}', tip: 'Chất xúc tác' },
          { label: '\\xrightarrow{\\text{xt, } t^{\\circ}}', code: '\\xrightarrow{\\text{xt, } t^{\\circ}}', display: '\\xrightarrow{\\text{xt, } t^{\\circ}}', tip: 'Xúc tác & nhiệt độ' }
        ]
      },
      {
        group: 'Ion & Chất phổ biến:',
        items: [
          { label: 'H_2O', code: '\\text{H}_2\\text{O}', display: '\\text{H}_2\\text{O}', tip: 'Nước' },
          { label: 'CO_2', code: '\\text{CO}_2', display: '\\text{CO}_2', tip: 'Khí carbonic' },
          { label: 'H^+', code: '\\text{H}^+', display: '\\text{H}^+', tip: 'Ion H+' },
          { label: 'OH^-', code: '\\text{OH}^-', display: '\\text{OH}^-', tip: 'Ion OH-' },
          { label: 'SO_4^{2-}', code: '\\text{SO}_4^{2-}', display: '\\text{SO}_4^{2-}', tip: 'Ion sunfat' },
          { label: 'CO_3^{2-}', code: '\\text{CO}_3^{2-}', display: '\\text{CO}_3^{2-}', tip: 'Ion cacbonat' },
          { label: 'NO_3^-', code: '\\text{NO}_3^-', display: '\\text{NO}_3^-', tip: 'Ion nitrat' },
          { label: 'Cl^-', code: '\\text{Cl}^-', display: '\\text{Cl}^-', tip: 'Ion clorua' },
          { label: 'Ca^{2+}', code: '\\text{Ca}^{2+}', display: '\\text{Ca}^{2+}', tip: 'Ion Canxi' },
          { label: 'Fe^{3+}', code: '\\text{Fe}^{3+}', display: '\\text{Fe}^{3+}', tip: 'Ion Sắt III' },
          { label: 'Al^{3+}', code: '\\text{Al}^{3+}', display: '\\text{Al}^{3+}', tip: 'Ion Nhôm' }
        ]
      },
      {
        group: 'Liên kết & Hữu cơ:',
        items: [
          { label: '-', code: '-', display: '-', tip: 'Liên kết đơn' },
          { label: '=', code: '=', display: '=', tip: 'Liên kết đôi' },
          { label: '\\equiv', code: '\\equiv', display: '\\equiv', tip: 'Liên kết ba' },
          { label: 'R-COOH', code: '\\text{R-COOH}', display: '\\text{R-COOH}', tip: 'Axit cacboxylic' },
          { label: 'R-OH', code: '\\text{R-OH}', display: '\\text{R-OH}', tip: 'Ancol' },
          { label: 'R-NH_2', code: '\\text{R-NH}_2', display: '\\text{R-NH}_2', tip: 'Amin' },
          { label: '_{6}^{12}C', code: '_{6}^{12}\\text{C}', display: '_{6}^{12}\\text{C}', tip: 'Đồng vị cacbon 12' },
          { label: '\\Delta H < 0', code: '\\Delta H < 0', display: '\\Delta H < 0', tip: 'Phản ứng tỏa nhiệt' },
          { label: '\\Delta H > 0', code: '\\Delta H > 0', display: '\\Delta H > 0', tip: 'Phản ứng thu nhiệt' }
        ]
      }
    ]
  },
  greek: {
    name: 'Ký tự Hy Lạp',
    icon: 'Ω',
    groups: [
      {
        group: 'Chữ thường:',
        items: [
          { label: '\\alpha', code: '\\alpha', display: '\\alpha', tip: 'alpha' },
          { label: '\\beta', code: '\\beta', display: '\\beta', tip: 'beta' },
          { label: '\\gamma', code: '\\gamma', display: '\\gamma', tip: 'gamma' },
          { label: '\\delta', code: '\\delta', display: '\\delta', tip: 'delta' },
          { label: '\\epsilon', code: '\\epsilon', display: '\\epsilon', tip: 'epsilon' },
          { label: '\\theta', code: '\\theta', display: '\\theta', tip: 'theta' },
          { label: '\\lambda', code: '\\lambda', display: '\\lambda', tip: 'lambda' },
          { label: '\\mu', code: '\\mu', display: '\\mu', tip: 'mu' },
          { label: '\\pi', code: '\\pi', display: '\\pi', tip: 'pi' },
          { label: '\\rho', code: '\\rho', display: '\\rho', tip: 'rho' },
          { label: '\\sigma', code: '\\sigma', display: '\\sigma', tip: 'sigma' },
          { label: '\\tau', code: '\\tau', display: '\\tau', tip: 'tau' },
          { label: '\\phi', code: '\\phi', display: '\\phi', tip: 'phi' },
          { label: '\\omega', code: '\\omega', display: '\\omega', tip: 'omega' }
        ]
      },
      {
        group: 'Chữ hoa:',
        items: [
          { label: '\\Delta', code: '\\Delta', display: '\\Delta', tip: 'Delta hoa' },
          { label: '\\Gamma', code: '\\Gamma', display: '\\Gamma', tip: 'Gamma hoa' },
          { label: '\\Theta', code: '\\Theta', display: '\\Theta', tip: 'Theta hoa' },
          { label: '\\Lambda', code: '\\Lambda', display: '\\Lambda', tip: 'Lambda hoa' },
          { label: '\\Sigma', code: '\\Sigma', display: '\\Sigma', tip: 'Sigma hoa' },
          { label: '\\Phi', code: '\\Phi', display: '\\Phi', tip: 'Phi hoa' },
          { label: '\\Omega', code: '\\Omega', display: '\\Omega', tip: 'Omega hoa' }
        ]
      }
    ]
  }
};
