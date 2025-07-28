from flask import Flask, render_template, request, jsonify
from sentence_transformers import SentenceTransformer, util
from flask_cors import CORS
import os
import fitz
import re

app = Flask(__name__)
CORS(app)

def dividir_texto_em_blocos_pequenos(texto, tamanho=200, sobreposicao=50):
    blocos = []
    start = 0
    while start < len(texto):
        fim = min(start + tamanho, len(texto))
        bloco = texto[start:fim].strip()
        if bloco:
            blocos.append(bloco)
        start += tamanho - sobreposicao
    return blocos

def extrair_blocos_dos_pdfs(pasta):
    blocos = []
    try:
        arquivos = os.listdir(pasta)
    except Exception as e:
        print(f"Erro ao listar a pasta '{pasta}': {e}")
        return blocos

    for nome_arquivo in arquivos:
        if nome_arquivo.lower().endswith('.pdf'):
            caminho = os.path.join(pasta, nome_arquivo)
            try:
                doc = fitz.open(caminho)
            except Exception as e:
                print(f"Erro ao abrir o arquivo '{nome_arquivo}': {e}")
                continue

            texto_pdf = ""
            for pagina in doc:
                texto_pdf += pagina.get_text()

            # Separar por parágrafos com ponto final
            paragrafos = re.split(r'\.\s*\n', texto_pdf)
            for p in paragrafos:
                p = p.strip()
                if p and p[-1] != '.':
                    p += '.'  # garantir que termina com ponto final
                blocos.append(p)

    blocos = list(dict.fromkeys(blocos))  # Remove duplicatas
    return blocos

print("Extraindo blocos dos PDFs...")
blocos = extrair_blocos_dos_pdfs("pdfs")
print(f"{len(blocos)} blocos de texto carregados.")

print("Carregando modelo de embeddings...")
modelo = SentenceTransformer('paraphrase-MiniLM-L6-v2')

print("Gerando embeddings dos blocos...")
embeddings = modelo.encode(blocos, convert_to_tensor=True)

respostas_customizadas = {
    "bom dia": "Bom dia! Como posso ajudar você hoje?",
    "boa tarde": "Boa tarde! Como posso ajudar você hoje?",
    "tudo bem": "Tudo sim! Como posso ajudar você hoje?",
    "quem é você": "Sou um chatbot desenvolvido pela DPIMA, criado para ajudar a esclarecer suas dúvidas.",
    "olá": "Olá! Como posso te ajudar hoje ?",
    "quem é seu criador": "Fui criado por Stanley, um desenvolvedor da DPIMA!",
    "quem te criou": "Fui desenvolvido por Stanley.",
    "tchau": "Até mais! Volte sempre que precisar.",
}

def resposta_customizada(pergunta):
    pergunta_lower = pergunta.lower()
    for chave in respostas_customizadas:
        if chave in pergunta_lower:
            return respostas_customizadas[chave]
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/perguntar', methods=['POST'])
def perguntar():
    dados = request.get_json()
    pergunta = dados.get('pergunta', '') if dados else ''

    if not pergunta.strip():
        return jsonify({'resposta': "Por favor, digite uma pergunta válida."})

    resposta = resposta_customizada(pergunta)
    if resposta:
        return jsonify({'resposta': resposta})

    pergunta_emb = modelo.encode(pergunta, convert_to_tensor=True)
    similaridades = util.cos_sim(pergunta_emb, embeddings)[0]

    limiar = 0.4
    blocos_filtrados = [(i, similaridades[i].item()) for i in range(len(similaridades)) if similaridades[i].item() > limiar]

    if not blocos_filtrados:
        return jsonify({'resposta': "Desculpe, não encontrei uma resposta clara nos documentos para essa pergunta."})

    blocos_filtrados.sort(key=lambda x: x[1], reverse=True)
    indice_top = blocos_filtrados[0][0]
    resposta_final = blocos[indice_top]

    return jsonify({'resposta': resposta_final})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
