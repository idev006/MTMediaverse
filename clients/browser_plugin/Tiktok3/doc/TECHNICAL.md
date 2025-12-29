# TikTok Uploader v5.1 - Technical Manual

## Architecture

```
TikTokUploader (Namespace)
├── State      → StateManager instance
├── Api        → ApiClient instance
├── Human      → HumanLike instance
├── Page       → PageHandler instance
├── Automation → AutomationEngine instance
└── init()     → Initialize app
```

## Namespace Pattern

All classes wrapped in IIFE:

```javascript
(function(TTU) {
    class MyClass { ... }
    TTU.MyClass = MyClass;
})(window.TikTokUploader || {});
```

## Classes

| Class | Role |
|-------|------|
| StateManager | Singleton state, observer pattern |
| ApiClient | API facade |
| HumanLike | Anti-bot utilities |
| PageHandler | DOM manipulation |
| AutomationEngine | Automation controller |

## Libraries

| Library | Version | Size |
|---------|---------|------|
| Vue.js | 3.x | 161 KB |
| Tailwind | CDN | ~100 KB |
| DaisyUI | 4.x | ~70 KB |

## Debug Console

```javascript
TikTokUploader.State       // State
TikTokUploader.Automation  // Engine
TTU.State.products         // Products
```

## Extension

```javascript
// Add new module
TTU.register('Analytics', new AnalyticsModule());

// Extend existing
TTU.extend('State', { newMethod() {} });
```
