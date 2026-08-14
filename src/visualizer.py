import json
import streamlit.components.v1 as components

def render_bpmn(xml_content):
    """Renders an interactive BPMN diagram using bpmn-js."""
    safe_xml = json.dumps(xml_content)
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8" />
      <link rel="stylesheet" href="https://unpkg.com/bpmn-js/dist/assets/diagram-js.css" />
      <link rel="stylesheet" href="https://unpkg.com/bpmn-js/dist/assets/bpmn-font/css/bpmn.css" />
      <style>
        html, body, #canvas {{ height: 100%; padding: 0; margin: 0; }}
      </style>
    </head>
    <body>
      <div style="position: relative; height: 600px; border: 1px solid #ccc; border-radius: 5px;">
        <div id="canvas" style="height: 100%; width: 100%;"></div>
        <div style="position: absolute; bottom: 20px; right: 20px; z-index: 10; display: flex; gap: 5px;">
          <button onclick="viewer.get('zoomScroll').stepZoom(1)" style="padding: 5px 10px; cursor: pointer;">Zoom In (+)</button>
          <button onclick="viewer.get('zoomScroll').stepZoom(-1)" style="padding: 5px 10px; cursor: pointer;">Zoom Out (-)</button>
          <button onclick="viewer.get('canvas').zoom('fit-viewport')" style="padding: 5px 10px; cursor: pointer;">Reset</button>
        </div>
      </div>
      <script src="https://unpkg.com/bpmn-js/dist/bpmn-navigated-viewer.production.min.js"></script>
      <script>
        var viewer = new BpmnJS({{ container: '#canvas' }});
        var xml = {safe_xml};
        viewer.importXML(xml).then(function(result) {{
          viewer.get('canvas').zoom('fit-viewport');
          
          // Allow zooming without Ctrl key
          document.getElementById('canvas').addEventListener('wheel', function(e) {{
            if (!e.ctrlKey) {{
              e.preventDefault();
              var zoomScroll = viewer.get('zoomScroll');
              var step = e.deltaY > 0 ? -0.5 : 0.5;
              zoomScroll.stepZoom(step, {{ x: e.offsetX, y: e.offsetY }});
            }}
          }});
          
        }}).catch(function(err) {{
          console.error('could not import BPMN 2.0 diagram', err);
        }});
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=620)
