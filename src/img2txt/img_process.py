from src.ocr.main import OCR
ocr_model = OCR()

def ocr_img(img_url):
    results = ocr_model(img_url)
    print(f"img file ocr ================================")
    result_str = ''
    for result in results[0]:
        result_str += result[1]
    return result_str
