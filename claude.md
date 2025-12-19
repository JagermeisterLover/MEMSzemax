# MEMS Pixel Controller Enhancement Requirements

## Overview
This document outlines the required enhancements to the MEMS Pixel Controller application (`MEMS.py`). The goal is to improve the drawing functionality, fix image loading issues, and update terminology to be more intuitive.

---

## 1. Drawing Functionality - Drag to Paint

**Current behavior**: Users must click each pixel individually to change its state.

**Required behavior**: Users should be able to draw by holding down the left mouse button (LMB) and dragging across the pixel grid.

### Implementation Requirements:
- Add mouse tracking to detect when LMB is held down
- Enable continuous painting while dragging across pixels
- The selected pen state should be applied to all pixels the mouse passes over
- Release LMB to stop painting
- This should work smoothly across the entire 64x48 grid

### Technical Details:
- Implement `mousePressEvent`, `mouseMoveEvent`, and `mouseReleaseEvent` handlers
- Track mouse button state to know when drawing is active
- Use `enterEvent` on PixelButton widgets to detect when mouse enters a pixel while drawing
- Ensure the grid accepts mouse tracking with `setMouseTracking(True)`

---

## 2. Pen Tool Selection

**Current behavior**: Clicking a pixel cycles through states (0 → 1 → 2 → 0).

**Required behavior**: Add a pen tool selector that allows users to choose which state (0, 1, or 2) they want to paint with.

### Implementation Requirements:
- Add a pen tool selector in the control panel (likely a ComboBox or radio buttons)
- Display the three states clearly:
  - State 0: Inactive (grey)
  - State 1: On (green)
  - State 2: Off (red)
- When clicking or dragging, apply the selected pen state to pixels
- Single-click should set the pixel to the selected pen state (no more cycling)
- The pen selection should be persistent across multiple drawing operations

### UI Location:
- Place the pen selector in the control panel, near the top for easy access
- Make it visually distinct so users understand it controls the drawing behavior

---

## 3. State Terminology Update

**Current terminology**:
- Angle 0 (State 0)
- Angle 1 (State 1): +angle
- Angle 2 (State 2): -angle

**Required terminology**:
- State 0: **Inactive** (grey)
- State 1: **On** (green)
- State 2: **Off** (red)

### Files to Update:
- `MEMS.py` - Update all UI labels and text references
  - Line 80: Update ComboBox items: `['0 (Off)', '1 (+angle)', '2 (-angle)']`
  - Lines 124, 133, 142: Update angle configuration labels
  - Lines 262-264: Update output text labels
  - Any comments or documentation

### Specific Changes:
- ComboBox should show: `['0 - Inactive (grey)', '1 - On (green)', '2 - Off (red)']`
- Angle configuration labels:
  - "Angle 0 (Inactive):"
  - "Angle 1 (On):"
  - "Angle 2 (Off):"
- Output text should reference states by their new names

---

## 4. Fix Image Loading - Vertical Flip Issue

**Current issue**: When loading an image, it appears vertically flipped (upside down).

**Root cause**: The image coordinate system needs to be corrected when mapping to MEMS pixel coordinates.

### Analysis:
Looking at lines 217-229 in `MEMS.py`:
- Image coordinates: (0,0) is top-left
- MEMS display: pixels are displayed with Y-axis inverted (line 106)
- The current code doesn't account for the vertical flip properly

### Fix Required:
- In the `load_image()` method around line 219-225, flip the Y-coordinate when reading from the image array
- Use `img_bw[self.y_pixels - 1 - y, x]` instead of `img_bw[y, x]`
- This will correctly map the image orientation to the display orientation

---

## 5. Image Color Mapping Update

**Current behavior**:
- Black pixels (dark) → State 0 (grey/inactive)
- White pixels (bright) → State 1 (green/on)

**Required behavior**:
- Black pixels (dark) → State 1 (green/On)
- White pixels (bright) → State 2 (red/Off)

### Implementation:
In `load_image()` method around line 228:
- Current: `state = 1 if img_value == 1 else 0`
- Required: `state = 2 if img_value == 1 else 1`
- Where `img_value == 1` means white (above threshold 128)
- And `img_value == 0` means black (below threshold 128)

### Logic:
- Black pixels (0 in thresholded array) → State 1 (On/green)
- White pixels (1 in thresholded array) → State 2 (Off/red)

---

## Implementation Checklist

### Phase 1: Terminology Updates
- [ ] Update state names throughout the code
- [ ] Update ComboBox items to show new terminology
- [ ] Update angle configuration labels
- [ ] Update output text to use new state names
- [ ] Update any tooltips or help text

### Phase 2: Image Loading Fixes
- [ ] Fix vertical flip by inverting Y-coordinate when reading image
- [ ] Update color mapping: black → On (1), white → Off (2)
- [ ] Test with various images to verify correct orientation and colors

### Phase 3: Drawing Functionality
- [ ] Add pen tool selector UI component
- [ ] Implement mouse tracking for drag painting
- [ ] Add mouse event handlers (press, move, release)
- [ ] Update pixel click behavior to use selected pen state
- [ ] Test drawing smoothly across the grid

### Phase 4: Testing
- [ ] Test single-click drawing with each pen state
- [ ] Test drag drawing with each pen state
- [ ] Test image loading with known images (verify orientation and colors)
- [ ] Test all existing functionality still works (Clear All, Fill All, Calculate, Copy)
- [ ] Test edge cases (dragging fast, dragging outside grid, etc.)

---

## Expected User Experience

After implementation:

1. **Drawing**: Users can select a pen tool (Inactive/On/Off) and paint by clicking or dragging
2. **States**: Clear, intuitive names (Inactive, On, Off) instead of technical terms
3. **Image Loading**: Images load in correct orientation with logical color mapping:
   - Dark/black areas become "On" (active/green)
   - Light/white areas become "Off" (inactive/red)
4. **Workflow**: Much faster pixel editing with drag-to-paint functionality

---

## Notes

- Maintain backward compatibility with existing parameter calculation logic
- Keep the same output format for Zemax parameters
- Ensure the grid display and coordinate system remain consistent
- All changes should be in `MEMS.py` only
