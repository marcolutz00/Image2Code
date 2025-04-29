# Manual Accessibility Test Catalog – Low‑Vision & Color‑Vision Focus

This README provides **eight manual checks** that complement automated accessibility testing tools (e.g. axe‑core). Each check maps to a WCAG 2.2 Success Criterion (SC) at Level A or AA that is *not* reliably caught by automation but is critical for users with low vision, color‑vision deficiencies or who rely on screen magnifiers.

**How to use**
> 1. Open the HTML page or component you want to audit.
> 2. Follow the **Test Steps** for each SC in order.
> 3. Record the result as `pass / fail` in your audit sheet. 
> 4. Any **fail** on Level A or **critical UX impact** should block release until fixed.

---

## 1  Text Resize (SC 1.4.4 AA)
|  |  |
|---|---|
| **Goal** | Text (excluding captions & images of text) can be resized to **200 %** without loss of content or functionality. |
| **Why it matters** | Users with low vision increase only text size rather than page zoom. Horizontal scrolling or clipped UI makes content unusable. |
| **Test Steps** | 1. Ctrl `+`/Cmd `+` until the browser shows **200 %**.<br>2. No horizontal scroll bar appears (except for data tables that *must* scroll both ways).<br>3. All functionality remains usable; no content overlaps or is cut off. |
| **Affected users** | Low‑vision, seniors |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/#resize-text> |

---

## 2  Reflow (SC 1.4.10 AA)
|  |  |
|---|---|
| **Goal** | Page must work with one‑directional scrolling at **320 px** width (portrait) or **256 px** height (landscape). |
| **Test Steps** | 1. Open DevTools → Responsive Mode → set width = 320 px.<br>2. Scroll vertically – **no horizontal scrolling** should be needed.<br>3. Interact with all controls; modals and menus must stay within viewport. |
| **Affected users** | Screen‑magnifier users, mobile readers |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/?showtechniques=1410#reflow> |

---

## 3  Non‑Text Contrast (SC 1.4.11 AA)
|  |  |
|---|---|
| **Goal** | UI component boundaries & focus indicators have **≥ 3 : 1** contrast ratio vs. adjacent colors. |
| **Test Steps** | 1. Identify buttons, form fields, toggles, focus rings.<br>2. With a color‑picker, sample foreground (border, icon, ring) and background.<br>3. Use a contrast checker (e.g. WebAIM) → ratio ≥ 3:1. |
| **Affected users** | Color‑blind and low‑vision users relying on visual cues |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/#non-text-contrast> |

---

## 4  Text Spacing (SC 1.4.12 AA)
|  |  |
|---|---|
| **Goal** | Content and functionality survive when user increases spacing via custom style sheet. |
| **Quick CSS Bookmarklet** |
| ```css
body, p, h1, h2, h3, h4, h5, h6 {
  line-height: 1.5 !important;
  letter-spacing: 0.12em !important;
  word-spacing: 0.16em !important;
  margin-bottom: 2em !important;
}
``` |
| **Test Steps** | 1. Inject the CSS above (Stylus plug‑in, DevTools > Sources > Snippets).<br>2. Verify no text overlaps, content disappears, or controls break. |
| **Affected users** | Low‑vision, dyslexic readers |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/#text-spacing> |

---

## 5  Keyboard & No‑Trap (SC 2.1.1 + 2.1.2 A)
|  |  |
|---|---|
| **Goal** | All functionality operable via keyboard; focus can always move away (no trap). |
| **Test Steps** | 1. Press **Tab** from top of page; reach every interactive element.<br>2. Use **Enter/Space/Arrow** keys per component specs.<br>3. In modals/menus, press **Esc** → focus returns to trigger. |
| **Affected users** | Screen‑magnifier & low‑vision users who combine keyboard + zoom |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/#keyboard> , <https://www.w3.org/WAI/WCAG22/quickref/#no-keyboard-trap> |

---

## 6  Focus Order (SC 2.4.3 A)
|  |  |
|---|---|
| **Goal** | Tabbing order matches visual/logical reading order. |
| **Test Steps** | 1. Run through **Tab** sequence.<br>2. Ensure order aligns with DOM & expected workflow (e.g. nav → search → main → sidebar). |
| **Affected users** | Low‑vision screen‑magnifier users |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/?showtechniques=247#focus-order> |

---

## 7  Headings & Labels (SC 2.4.6 AA)
|  |  |
|---|---|
| **Goal** | Headings and form labels clearly describe topic or purpose. |
| **Test Steps** | 1. Visually scan H1‑H6 – hierarchy reflects content structure.<br>2. Inspect form labels: describe input purpose; no missing `<label>`.<br>3. Hidden labels (`aria-label`) still announced by screenreader. |
| **Affected users** | Screen‑reader & low‑vision users (quick page overview) |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/#headings-and-labels> |

---

## 8  Focus Visible (SC 2.4.7 AA)
|  |  |
|---|---|
| **Goal** | Keyboard focus indicator is always visible and has sufficient contrast. |
| **Test Steps** | 1. Tab to each control – visible ring/border appears.<br>2. Check CSS: `outline: none` must not remove visibility without alternative.<br>3. Contrast ratio of focus style ≥ 3:1 vs. adjacent colors. |
| **Affected users** | Low‑vision keyboard users |
| **Reference** | <https://www.w3.org/WAI/WCAG22/quickref/#focus-visible> |

---

## Logging Template

```json
{
  "page": "https://example.com/register",
  "manual_checks": {
    "1.4.4": "fail",
    "1.4.10": "pass",
    "1.4.11": "needs-review",
    "1.4.12": "pass",
    "2.1.1": "pass",
    "2.4.3": "pass",
    "2.4.6": "pass",
    "2.4.7": "fail"
  },
  "comments": {
    "1.4.4": "Horizontal scroll appears in hero carousel at 200% zoom.",
    "2.4.7": "Focus ring removed via outline:none on primary CTA buttons."
  }
}
```

> **Tip**  Integrate this README directly into your Docker image at `/AUDIT/README.md`; mount the folder when launching the container so auditors always have the latest checklist at hand.

