"""Inline models/*.glb into index.html between <!--MODELS--> markers as base64."""
import base64, glob, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = os.path.join(root, "index.html")
s = open(html, encoding="utf-8").read()
parts = []
for f in sorted(glob.glob(os.path.join(root, "models", "*.glb"))):
    k = os.path.splitext(os.path.basename(f))[0]
    parts.append(f'{k}:"{base64.b64encode(open(f,"rb").read()).decode()}"')
block = "<!--MODELS-->\n<script>window.VET_MODELS={" + ",".join(parts) + "};</script>\n<!--/MODELS-->"
s = re.sub(r"<!--MODELS-->[\s\S]*?<!--/MODELS-->", lambda m: block, s)
open(html, "w", encoding="utf-8").write(s)
print("embedded", len(parts), "models;", len(s)//1024, "KB total")
