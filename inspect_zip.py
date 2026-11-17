import zipfile
import os
import glob
import xml.etree.ElementTree as ET

user_dir = r"C:/Users/PRADNYAN/.gemini/antigravity/brain/34bdfbfa-55ef-40c3-a92e-ba02dc334265/.user_uploaded"
zips = glob.glob(os.path.join(user_dir, "*.zip"))
print("Found zip files:")
for zf in sorted(zips, key=os.path.getmtime, reverse=True):
    print(" -", zf, f"({os.path.getsize(zf)} bytes)")

target_zip = r"C:/Users/PRADNYAN/.gemini/antigravity/brain/34bdfbfa-55ef-40c3-a92e-ba02dc334265/.user_uploaded/media_1794688178342_f3d17a91.zip"
if not os.path.exists(target_zip) and zips:
    target_zip = sorted(zips, key=os.path.getmtime, reverse=True)[0]

out_dir = os.path.join(os.path.dirname(__file__), "unzipped_doc")
os.makedirs(out_dir, exist_ok=True)
manifest_path = os.path.join(os.path.dirname(__file__), "extracted_manifest.txt")
text_dump_path = os.path.join(os.path.dirname(__file__), "extracted_document_text.txt")

extracted_files = []
if os.path.exists(target_zip):
    print(f"\nExtracting {target_zip}...")
    with zipfile.ZipFile(target_zip, 'r') as z:
        for name in z.namelist():
            extracted_files.append(name)
            print("  --> Extracted:", name)
        z.extractall(out_dir)

# Also check all files inside out_dir
all_extracted = []
for root, dirs, files in os.walk(out_dir):
    for f in files:
        all_extracted.append(os.path.join(root, f))

with open(manifest_path, "w", encoding="utf-8") as mf:
    mf.write("Extracted Files:\n")
    for fp in all_extracted:
        mf.write(f"- {fp} ({os.path.getsize(fp)} bytes)\n")

# Extract readable text from whatever was unzipped
doc_text = []
for fp in all_extracted:
    ext = os.path.splitext(fp)[1].lower()
    doc_text.append(f"\n==================== FILE: {os.path.basename(fp)} ====================\n")
    if ext in [".txt", ".md", ".json", ".csv", ".py", ".xml"]:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                doc_text.append(f.read())
        except Exception as e:
            doc_text.append(f"[Could not read as text: {e}]")
    elif ext == ".docx":
        try:
            with zipfile.ZipFile(fp) as docx_zip:
                xml_content = docx_zip.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                paragraphs = []
                for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                doc_text.append("\n".join(paragraphs))
        except Exception as e:
            doc_text.append(f"[Could not extract text from docx: {e}]")
    else:
        # Try reading first 50KB as text or strings
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(50000)
                doc_text.append(content)
        except Exception as e:
            doc_text.append(f"[Binary file: {os.path.basename(fp)}]")

with open(text_dump_path, "w", encoding="utf-8") as tf:
    tf.write("\n".join(doc_text))

print(f"\nManifest written to: {manifest_path}")
print(f"Document text dump written to: {text_dump_path}")
