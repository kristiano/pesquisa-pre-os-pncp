from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import datetime
from .analise_precos import analisar_precos

app = FastAPI(title="API de Pesquisa de Preços (PNCP + LLM)")

class PesquisaRequest(BaseModel):
    objeto: str
    llm_api_key: str
    quantidade_itens: int = 10

# Rota para se o usuário abrir o link da API direto no navegador por engano
@app.get("/")
@app.get("/api")
@app.get("/api/pesquisa")
def aviso_navegador():
    return {"status": "A API está online! Acesse a página principal para fazer a pesquisa."}

# Aceita tanto com o /api quanto sem o /api (resolve o problema de rota da Vercel)
@app.post("/api/pesquisa")
@app.post("/pesquisa")
def realizar_pesquisa(req: PesquisaRequest):
    """
    Realiza a busca no PNCP usando a Chave de API da LLM enviada pelo usuário via Frontend.
    """
    try:
        # A chave enviada pelo usuário está disponível em:
        chave_do_usuario = req.llm_api_key
        
        # =====================================================================
        # ESPAÇO PARA A LLM 
        # =====================================================================
        # Aqui você usa a 'chave_do_usuario' para fazer a requisição à LLM (ex: openai.api_key = chave_do_usuario)
        # e melhorar a string req.objeto.
        
        termo_refinado_pela_llm = req.objeto 
        
        # 1. Consulta à API do PNCP (itens de contratações)
        url_pncp = f"https://pncp.gov.br/api/search/?q={termo_refinado_pela_llm}&tipos_documento=item_contratacao&ordenacao=-data_atualizacao"
        headers = {'accept': 'application/json'}
        resp = requests.get(url_pncp, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro ao consultar o PNCP")
        
        dados = resp.json()
        itens = dados.get('items', [])
        
        # 2. Formatar os registros capturados
        registros = []
        for item in itens[:req.quantidade_itens]:
            valor = item.get('valor_unitario_estimado')
            if not valor or valor <= 0:
                continue
                
            orgao = item.get('orgao_entidade', {}).get('razao_social', 'Órgão não identificado')
            cnpj = item.get('orgao_entidade', {}).get('cnpj', '')
            ano = item.get('ano_compra', '')
            seq = item.get('sequencial_compra', '')
            link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
            
            registros.append({
                "objeto": item.get('descricao', termo_refinado_pela_llm),
                "valor": float(valor),
                "fonte": f"PNCP - {orgao}",
                "link": link,
                "data_acesso": datetime.datetime.now().strftime("%d/%m/%Y")
            })
            
        # =====================================================================
        # ESPAÇO PARA A LLM 2
        # =====================================================================
        # Usar a 'chave_do_usuario' para filtrar os dados em 'registros' com base na regra do tripé.
        
        # 3. Análise Estatística usando a lógica em Python
        estatisticas = analisar_precos(registros)
        
        return {
            "sucesso": True,
            "registros": registros,
            "estatisticas": estatisticas,
            "termo_buscado": termo_refinado_pela_llm
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
