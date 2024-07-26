# Interactions

The `interactions` option in Pixashot allows you to define a series of actions to be performed on the webpage before capturing the screenshot. This feature is useful for scenarios where you need to interact with the page, such as clicking buttons, filling forms, or waiting for specific elements to appear.

## Usage

The `interactions` option is an array of interaction steps. Each step is an object that defines a specific action to be performed.

## Available Interaction Steps

1. **Click**
   - Action: `"click"`
   - Selector: CSS selector of the element to click

2. **Type**
   - Action: `"type"`
   - Selector: CSS selector of the input element
   - Text: The text to type

3. **Hover**
   - Action: `"hover"`
   - Selector: CSS selector of the element to hover over

4. **Scroll**
   - Action: `"scroll"`
   - X: Horizontal scroll position
   - Y: Vertical scroll position

5. **Wait For**
   - Action: `"wait_for"`
   - Wait For: An object specifying what to wait for
     - Type: `"network_idle"`, `"network_mostly_idle"`, `"selector"`, or `"timeout"`
     - Value: Depends on the type (see examples below)

## Examples

### Click a Button

```json
{
  "url": "https://example.com",
  "interactions": [
    {
      "action": "click",
      "selector": "#submit-button"
    }
  ]
}
```

### Fill a Form

```json
{
  "url": "https://example.com/form",
  "interactions": [
    {
      "action": "type",
      "selector": "#username",
      "text": "johndoe"
    },
    {
      "action": "type",
      "selector": "#password",
      "text": "secretpassword"
    },
    {
      "action": "click",
      "selector": "#login-button"
    }
  ]
}
```

### Wait for Network Idle

```json
{
  "url": "https://example.com",
  "interactions": [
    {
      "action": "wait_for",
      "wait_for": {
        "type": "network_idle",
        "value": 5000
      }
    }
  ]
}
```

### Wait for an Element

```json
{
  "url": "https://example.com",
  "interactions": [
    {
      "action": "wait_for",
      "wait_for": {
        "type": "selector",
        "value": "#dynamic-content"
      }
    }
  ]
}
```

### Complex Interaction Sequence

```json
{
  "url": "https://example.com/shop",
  "interactions": [
    {
      "action": "click",
      "selector": "#category-dropdown"
    },
    {
      "action": "wait_for",
      "wait_for": {
        "type": "selector",
        "value": "#category-list"
      }
    },
    {
      "action": "click",
      "selector": "#category-list .electronics"
    },
    {
      "action": "wait_for",
      "wait_for": {
        "type": "network_mostly_idle",
        "value": 3000
      }
    },
    {
      "action": "scroll",
      "x": 0,
      "y": 500
    },
    {
      "action": "hover",
      "selector": "#product-card-1"
    },
    {
      "action": "wait_for",
      "wait_for": {
        "type": "timeout",
        "value": 1000
      }
    }
  ]
}
```

## Notes

- The interactions are performed in the order they are specified.
- If an interaction fails (e.g., a selector is not found), the capture process will throw an error.
- Use the `wait_for` action judiciously to ensure the page is in the desired state before proceeding with the next action or capturing the screenshot.
- The `interactions` option can be combined with other Pixashot options like `full_page`, `format`, etc.

Remember to test your interaction sequences thoroughly, especially when dealing with dynamic content or complex user interfaces.