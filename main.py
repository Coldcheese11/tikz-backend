from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os
import base64

app = FastAPI(title="TikZ Render Engine")

# Cho phép trang web React của bạn (từ Vercel) gọi sang API này
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TikzRequest(BaseModel):
    tikz_codes: list[str]

@app.post("/render")
async def render_tikz(request: TikzRequest):
    results = []
    
    for code in request.tikz_codes:
        latex_doc = f"""
\\documentclass[tikz, border=2pt]{{standalone}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath, amssymb, amsfonts}}
\\usepackage{{tkz-euclide}}
\\usepackage{{tkz-tab}} % Hỗ trợ vẽ Bảng biến thiên, Bảng xét dấu
\\usepackage{{pgfplots}}
\\usetikzlibrary{{arrows, arrows.meta, calc, patterns, shapes.geometric, positioning, intersections, quotes, angles}}
\\pgfplotsset{{compat=1.18}}
\\begin{{document}}
{code}
\\end{{document}}
"""
        # Tạo thư mục tạm thời trên RAM để xử lý (Xử lý xong tự xóa, không bị rác server)
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = os.path.join(tmpdir, 'code.tex')
            pdf_file = os.path.join(tmpdir, 'code.pdf')
            svg_file = os.path.join(tmpdir, 'code.svg')

            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_doc)

            try:
                # Bước 1: Gọi hệ điều hành chạy pdflatex để biến TeX thành PDF
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'code.tex'], 
                    cwd=tmpdir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                # Bước 2: Ép PDF thành ảnh vector SVG (siêu nét)
                subprocess.run(['pdf2svg', 'code.pdf', 'code.svg'], cwd=tmpdir, check=True)
                
                # Bước 3: Đọc file SVG và mã hóa thành chuỗi Base64 trả thẳng về Frontend
                with open(svg_file, 'rb') as f:
                    svg_data = f.read()
                    b64_svg = base64.b64encode(svg_data).decode('utf-8')
                    results.append(f"data:image/svg+xml;base64,{b64_svg}")
                    
            except subprocess.CalledProcessError as e:
                # Nếu code TikZ của giáo viên gõ sai, trả về cờ ERROR
                print("Lỗi biên dịch:", e.stderr.decode('utf-8', errors='ignore'))
                results.append("ERROR")
                
    return {"images": results}

@app.get("/")
def health_check():
    return {"status": "ok", "message": "TikZ Render Engine is running"}
