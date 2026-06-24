import time
from PyQt6.QtCore import QObject, pyqtSignal, QEventLoop, Qt, QThread

# JS Utils prefix to inject selectors resolution
JS_UTILS = """
var _utils = {
    getElement: function(sel) {
        if (!sel) return null;
        if (sel.startsWith('xpath=')) {
            var path = sel.substring(6);
            try {
                var result = document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                return result.singleNodeValue;
            } catch(e) { return null; }
        } else if (sel.startsWith('css=')) {
            return document.querySelector(sel.substring(4));
        } else {
            return document.querySelector(sel);
        }
    },
    getElements: function(sel) {
        if (!sel) return [];
        if (sel.startsWith('xpath=')) {
            var path = sel.substring(6);
            try {
                var iterator = document.evaluate(path, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
                var nodes = [];
                var node = iterator.iterateNext();
                while (node) {
                    nodes.push(node);
                    node = iterator.iterateNext();
                }
                return nodes;
            } catch(e) { return []; }
        } else if (sel.startsWith('css=')) {
            return Array.from(document.querySelectorAll(sel.substring(4)));
        } else {
            return Array.from(document.querySelectorAll(sel));
        }
    },
    click: function(el) {
        if (!el) return;
        var target = el;
        try {
            var rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                var x = rect.left + rect.width / 2;
                var y = rect.top + rect.height / 2;
                var hit = document.elementFromPoint(x, y);
                if (hit && (el.contains(hit) || hit === el)) {
                    target = hit;
                }
            }
        } catch(e) {}
        
        var events = ['mousedown', 'mouseup'];
        for (var i = 0; i < events.length; i++) {
            var ev = new MouseEvent(events[i], {
                bubbles: true,
                cancelable: true,
                view: window,
                buttons: 1
            });
            target.dispatchEvent(ev);
        }
        
        if (typeof target.click === 'function') {
            target.click();
        } else {
            target.dispatchEvent(new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            }));
        }
    }
};
"""

class JSBridge(QObject):
    run_js_signal = pyqtSignal(str, dict)

    def __init__(self, page=None):
        super().__init__()
        self.page = page
        self.run_js_signal.connect(self._handle_run_js, Qt.ConnectionType.BlockingQueuedConnection)

    def set_page(self, page):
        self.page = page

    def _handle_run_js(self, script, result_container):
        if not self.page:
            result_container['result'] = None
            return

        loop = QEventLoop()
        result = None
        finished = False

        def callback(val):
            nonlocal result, finished
            result = val
            finished = True
            loop.quit()

        self.page.runJavaScript(script, callback)

        # Wait for the callback to fire, processing events
        if not finished:
            loop.exec()

        result_container['result'] = result

    def execute_js(self, script):
        container = {}
        # Prepend the utilities prefix to every executed script so _utils is available
        full_script = JS_UTILS + "\n" + script
        self.run_js_signal.emit(full_script, container)
        return container.get('result')

    def click(self, selector):
        sel = selector.replace('"', '\\"')
        script = f"""
        (function() {{
            var el = _utils.getElement("{sel}");
            if (el) {{
                _utils.click(el);
                return true;
            }}
            return false;
        }})()
        """
        return bool(self.execute_js(script))

    def is_visible(self, selector):
        sel = selector.replace('"', '\\"')
        script = f"""
        (function() {{
            var el = _utils.getElement("{sel}");
            if (el) {{
                var style = window.getComputedStyle(el);
                return el.offsetWidth > 0 && 
                       el.offsetHeight > 0 && 
                       style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0';
            }}
            return false;
        }})()
        """
        return bool(self.execute_js(script))

    def get_text(self, selector):
        sel = selector.replace('"', '\\"')
        script = f"""
        (function() {{
            var el = _utils.getElement("{sel}");
            return el ? el.innerText : null;
        }})()
        """
        return self.execute_js(script)

    def get_value(self, selector):
        sel = selector.replace('"', '\\"')
        script = f"""
        (function() {{
            var el = _utils.getElement("{sel}");
            return el ? el.value : null;
        }})()
        """
        return self.execute_js(script)

    def set_value(self, selector, value):
        sel = selector.replace('"', '\\"')
        val = value.replace('"', '\\"').replace('\n', '\\n')
        script = f"""
        (function() {{
            var el = _utils.getElement("{sel}");
            if (el) {{
                el.value = "{val}";
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
        }})()
        """
        return bool(self.execute_js(script))

    def select_option(self, selector, value):
        sel = selector.replace('"', '\\"')
        val = value.replace('"', '\\"')
        script = f"""
        (function() {{
            var el = _utils.getElement("{sel}");
            if (el && el.tagName === 'SELECT') {{
                el.value = "{val}";
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
        }})()
        """
        return bool(self.execute_js(script))

    def wait_for_selector(self, selector, timeout_ms=10000):
        # Poll every 250ms
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout_ms:
            if self.is_visible(selector):
                return True
            QThread.msleep(250)
        return False
