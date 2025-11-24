import fitz  # PyMuPDF
import sys
import os

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return str(e)
        print(text)

if __name__ == "__main__":
    pdf_path = "cvs/CV_11_11_2025 (1) copy.pdf"
    output_dir = "extracted_cvs"
    
    if os.path.exists(pdf_path):
        # Extract text
        extracted_text = extract_text_from_pdf(pdf_path)
        
        # Print to console
        print(extracted_text)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename based on input PDF name
        pdf_filename = os.path.basename(pdf_path)
        txt_filename = os.path.splitext(pdf_filename)[0] + ".txt"
        output_path = os.path.join(output_dir, txt_filename)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        print(f"\n\nExtracted text saved to: {output_path}")
    else:
        print(f"File not found: {pdf_path}")
