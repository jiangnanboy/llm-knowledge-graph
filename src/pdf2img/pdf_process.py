#-*-coding:utf-8 -*-
import fitz
from PIL import Image


def pdf_img(pdf_path):
    '''
    process pdf image
    :param pdf_path:
    :return:
    '''
    pdf_filename = pdf_path.split('\\')[-1][:-4]
    pdf_doc = fitz.open(pdf_path)
    pdf_imgs = []
    for pg_num in range(pdf_doc.page_count):
        page = pdf_doc[pg_num]
        mat = fitz.Matrix(3, 3)
        pix = page.get_pixmap(matrix=mat)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        pdf_imgs.append(image)
        print(f"Pdf file [{pdf_filename}.pdf] Processed page {pg_num + 1}================================")
    pdf_doc.close()
    return pdf_imgs

