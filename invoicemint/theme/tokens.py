# Design tokens used by ttk styles
TOKENS_LIGHT = {
"color": {
"bg": "#F7F9FC",
"surface": "#FFFFFF",
"surface_alt": "#F1F4F8",
"text": "#1F2937",
"text_muted": "#6B7280",
"border": "#E5E7EB",
"accent": "#3A86FF",
"accent_text": "#FFFFFF",
},
"space": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24},
}


TOKENS_DARK = {
**TOKENS_LIGHT,
"color": {
**TOKENS_LIGHT["color"],
"bg": "#0F172A",
"surface": "#111827",
"surface_alt": "#1F2937",
"text": "#E5E7EB",
"text_muted": "#9CA3AF",
"border": "#374151",
},
}