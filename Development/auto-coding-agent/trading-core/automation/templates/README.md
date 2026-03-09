# UI Templates Directory

This directory contains template images for UI element recognition.

## Template Naming Convention

Use descriptive names for UI elements:

### Trading Buttons
- `buy_button.png` - Buy (买入) button
- `sell_button.png` - Sell (卖出) button
- `cancel_button.png` - Cancel (撤单) button
- `confirm_button.png` - Confirm (确认) button

### Input Fields
- `stock_code_input.png` - Stock code input field
- `price_input.png` - Price input field
- `quantity_input.png` - Quantity input field
- `password_input.png` - Password input field

### UI Elements
- `position_tab.png` - Position (持仓) tab
- `order_tab.png` - Order (委托) tab
- `trade_tab.png` - Trade (交易) tab
- `refresh_button.png` - Refresh (刷新) button

## Creating Templates

Run the manual region selection test:

```bash
python tests/test_window_recognition.py --test manual
```

This will:
1. Display the Tonghuashun window screenshot
2. Allow you to select a region with mouse drag
3. Save the selected region as a template
4. Save the coordinates to coordinates.json

## Template Format

Each template file should have a corresponding `.txt` description file:

```
buy_button.png
buy_button.txt  <- Description file
```

Example description:
```
买入按钮
位置：交易面板右上角
颜色：红色背景，白色文字
尺寸：约 80x40 像素
```

## Tips for Good Templates

1. **Unique Features**: Capture unique visual features of the element
2. **Minimal Background**: Include minimal surrounding area
3. **Consistent State**: Templates should match the actual UI state
4. **Lighting**: Avoid shadows or reflections
5. **Resolution**: Use native screen resolution
