APP_CSS = """
App {
    background: #0a0d12;
    color: #dde5f2;
}
Screen {
    layout: vertical;
}
Header, Footer {
    background: #111826;
    color: #dde5f2;
}
#main {
    layout: grid;
    grid-size: 3;
    grid-columns: 1fr 1fr 1.2fr;
    height: 1fr;
    background: #0a0d12;
}
.pane {
    background: #0e1420;
    color: #dde5f2;
    overflow: hidden;
    padding: 0 1;
}
.pane.right-divider {
    border-right: solid #243248;
}
.pane:focus-within {
    background: #121b2a;
}
.pane-title {
    height: 1;
    color: #96acd2;
    text-style: bold;
}
#log_meta {
    height: 1;
    color: #90a4c6;
}
#devices, #gatt, #log {
    background: #0e1420;
    color: #dde5f2;
}
#status {
    height: 1;
    background: #15263f;
    color: #ffffff;
    padding: 0 1;
}
DataTable {
    background: #0e1420;
    color: #dde5f2;
}
Tree {
    background: #0e1420;
    color: #dde5f2;
}
RichLog {
    background: #0e1420;
    color: #dde5f2;
}
#latest_value_scroll {
    max-height: 20;
    border: solid #243248;
    margin-bottom: 1;
}
#latest_value_scroll.expanded {
    max-height: 100%;
}

#latest_value {
    padding: 1;
}
.history-title {
    height: 1;
    color: #96acd2;
    text-style: bold;
}
#log.collapsed {
    max-height: 3;
}
"""
