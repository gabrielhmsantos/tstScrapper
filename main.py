import os.path

import requests
from datetime import datetime, timedelta
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
import re

from fastapi import FastAPI, HTTPException


def split_and_save_combined_pages(input_file, output_file):
    with open(input_file, 'rb') as file:
        pdf_reader = PdfReader(file)
        pdf_writer = PdfWriter()

        for page_number in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_number]

            # Obtém a largura da página
            width = page.mediabox.upper_right[0]

            # Divide a página ao meio
            half_width = width / 2

            # Cria duas páginas, uma para o lado esquerdo e outra para o lado direito
            left_page = PdfWriter()
            right_page = PdfWriter()

            # Adiciona a parte correspondente para cada página
            left_page.add_page(page)
            left_page.pages[0].mediabox.upper_right = (half_width, page.mediabox.upper_right[1])

            right_page.add_page(page)
            right_page.pages[0].mediabox.upper_left = (half_width, page.mediabox.upper_left[1])

            # Adiciona as páginas à ordem correta
            pdf_writer.add_page(left_page.pages[0])
            pdf_writer.add_page(right_page.pages[0])

        # Salva o arquivo de saída
        with open(output_file, 'wb') as output:
            pdf_writer.write(output)

def extract_processes(input_file, numero_oab):
    processes = []
    with fitz.open(input_file) as doc:
        for page_number in range(doc.page_count):
            page = doc[page_number]
            text = page.get_text()
            # Use expressão regular para encontrar todos os processos na página
            # Crie a expressão regular com a variável
            padrao_regex = r"Processo Nº[\s\S]*?" + numero_oab.replace("/", r"\/") + r"[\s\S]*?Intimado"
            matches = re.findall(padrao_regex, text)
            if matches:
                for match in matches:
                    padrao_regex = r"Processo Nº\s*([\w.-]+)"
                    num_processo = re.match(padrao_regex, match)
                    num_processo = num_processo.group(1).strip()
                    if num_processo not in processes:
                        processes.append(num_processo)
    return processes


app = FastAPI()

@app.get("/get_processes")
def get_processes(numero_oab: str = '84438/RS'):
    url = "https://diario.jt.jus.br/cadernos/Diario_J_TST.pdf"

    data_diario = datetime.now() - timedelta(days=1)
    data_diario = data_diario.strftime("%Y-%m-%d")

    source_file = f"diario_tst_download.pdf"
    dest_file = f"diario_tst.pdf"

    if not os.path.exists(dest_file):

        response = requests.get(url)

        if response.status_code == 200:
            with open(source_file, 'wb') as file:
                file.write(response.content)
            split_and_save_combined_pages(source_file, dest_file)
            print(f"O PDF foi baixado com sucesso como {dest_file}")
            os.remove(source_file)
        else:
            print(f"Erro ao baixar o PDF. Código de status: {response.status_code}")

    extracted_processes = extract_processes(dest_file, numero_oab=numero_oab)

    # Retorna os processos encontrados
    if not extracted_processes:
        raise HTTPException(status_code=204, detail="No content")
    return extracted_processes


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
