from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import requests
import uvicorn

app = FastAPI(
    title="API Explorer JW",
    description="API definitiva de mídias com navegação de pastas, busca, Fallback de Imagens, Duração e Datas.",
    version="3.5.0"
)

MEDIATOR_BASE_URL = "https://b.jw-cdn.org/apis/mediator/v1"

# ==========================================
# Funções Auxiliares (Extratores e Formatadores)
# ==========================================
def extrair_melhor_imagem(imagens: dict, tamanho_preferido: str = "lg") -> str:
    if not imagens:
        return ""
    formatos_prioritarios = ["sqr", "lsr", "pnt", "wss"]
    for formato in formatos_prioritarios:
        if formato in imagens and tamanho_preferido in imagens[formato]:
            return imagens[formato][tamanho_preferido]
    for formato in formatos_prioritarios:
        if formato in imagens:
            for t in ["xl","lg", "md", "sm", "xs"]:
                if t in imagens[formato]:
                    return imagens[formato][t]
    for formato, tamanhos in imagens.items():
        if isinstance(tamanhos, dict) and tamanhos:
            return list(tamanhos.values())[0]
    return ""

def extrair_todos_arquivos(arquivos: list) -> list:
    arquivos_extraidos = []
    urls_vistas = set()
    for arq in arquivos:
        url = str(arq.get("progressiveDownloadURL", ""))
        if not url or url in urls_vistas:
            continue
        urls_vistas.add(url)
        formato = url.split('.')[-1].lower() if '.' in url else "desconhecido"
        tamanho_mb = round(arq.get("filesize", 0) / (1024 * 1024), 2)
        resolucao = arq.get("frameHeight", None)
        arquivos_extraidos.append({
            "formato": formato,
            "resolucao": resolucao,
            "tamanho_mb": tamanho_mb,
            "duracao_segundos": arq.get("duration", 0),
            "url_download": url
        })
    arquivos_extraidos.sort(key=lambda x: (x["resolucao"] or 0), reverse=True)
    return arquivos_extraidos

def obter_imagem_fallback(chave: str, idioma: str) -> str:
    url = f"{MEDIATOR_BASE_URL}/categories/{idioma}/{chave}?detailed=1"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code == 200:
            dados = resp.json().get("category", {})
            
            img = extrair_melhor_imagem(dados.get("images", {}), "xl")
            if img: return img
            
            midias = dados.get("media", [])
            if midias:
                img = extrair_melhor_imagem(midias[0].get("images", {}), "xl")
                if img: return img
                
            subs = dados.get("subcategories", [])
            if subs:
                img = extrair_melhor_imagem(subs[0].get("images", {}), "xl")
                if img: return img
    except:
        pass
    return ""

def fazer_requisicao(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resposta = requests.get(url, headers=headers)
    if resposta.status_code != 200:
        raise HTTPException(
            status_code=resposta.status_code, 
            detail="Não foi possível acessar os dados no servidor remoto."
        )
    return resposta.json()

def formatar_data(data_iso: str) -> str:
    """Converte datas no formato YYYY-MM-DD para DD/MM/YYYY"""
    if not data_iso:
        return ""
    try:
        apenas_data = data_iso.split("T")[0]
        ano, mes, dia = apenas_data.split("-")
        return f"{dia}/{mes}/{ano}"
    except:
        return data_iso

def formatar_duracao(segundos) -> str:
    """Converte segundos totais em MM:SS ou HH:MM:SS"""
    try:
        seg = int(float(segundos))
        minutos = seg // 60
        segundos_rest = seg % 60
        if minutos >= 60:
            horas = minutos // 60
            minutos_rest = minutos % 60
            return f"{horas}:{minutos_rest:02d}:{segundos_rest:02d}"
        return f"{minutos}:{segundos_rest:02d}"
    except:
        return ""

# ==========================================
# Rotas da API (Back-end)
# ==========================================
@app.get("/api/explorar", summary="Navegador unificado de Pastas e Arquivos")
def explorar_diretorio(
    pasta: str = Query(None, description="Deixe vazio para a Raiz ou passe a chave (Ex: Audio, VODMovies)"),
    idioma: str = Query("T", description="Letra do idioma no JW (Ex: T para português)")
):
    conteudo = []
    nome_atual = ""
    
    # 1. TRATAMENTO DA RAIZ (Criando a Pasta Virtual)
    if not pasta:
        url = f"{MEDIATOR_BASE_URL}/categories/{idioma}?detailed=1"
        dados = fazer_requisicao(url)
        categorias = dados.get("categories", [])
        nome_atual = "Raiz do Servidor"
        
        destaque_adicionado = False
        chaves_destaque = ["FeaturedLibraryVideos", "FeaturedLibraryLanding", "FeaturedSetTopBoxes"]
        
        for cat in categorias:
            chave = cat.get("key")
            imagens = cat.get("images", {})
            
            if chave in chaves_destaque:
                if not destaque_adicionado:
                    imagem_final = extrair_melhor_imagem(imagens, tamanho_preferido="xl")
                    if not imagem_final:
                        imagem_final = obter_imagem_fallback(chave, idioma)
                        
                    conteudo.append({
                        "tipo": "pasta",
                        "nome": "⭐ Em Destaque",
                        "chave": "MergedFeatured",
                        "tem_subpastas": False,
                        "imagem": imagem_final
                    })
                    destaque_adicionado = True
            else:
                imagem_final = extrair_melhor_imagem(imagens, tamanho_preferido="xl")
                if not imagem_final:
                    imagem_final = obter_imagem_fallback(chave, idioma)
                    
                conteudo.append({
                    "tipo": "pasta",
                    "nome": cat.get("name", "Sem Nome"),
                    "chave": chave,
                    "tem_subpastas": cat.get("hasSubcategories", False),
                    "imagem": imagem_final
                })
                
    # 2. TRATAMENTO DA PASTA VIRTUAL (Mesclando os vídeos sem repetir)
    elif pasta == "MergedFeatured":
        nome_atual = "⭐ Em Destaque"
        chaves_destaque = ["FeaturedLibraryVideos", "FeaturedLibraryLanding", "FeaturedSetTopBoxes"]
        
        midias_mescladas = []
        ids_vistos = set()
        
        for chave in chaves_destaque:
            url = f"{MEDIATOR_BASE_URL}/categories/{idioma}/{chave}?detailed=1"
            try:
                dados = fazer_requisicao(url)
                itens = dados.get("category", {}).get("media", [])
                
                for item in itens:
                    identificador = item.get("guid", item.get("title", ""))
                    if identificador not in ids_vistos:
                        ids_vistos.add(identificador)
                        midias_mescladas.append(item)
            except:
                pass
                
        for item in midias_mescladas:
            lista_arquivos = extrair_todos_arquivos(item.get("files", []))
            if lista_arquivos:
                data_bruta = item.get("firstPublished", item.get("datetime", ""))
                duracao_api = item.get("durationFormattedHHMM")
                duracao_seg = lista_arquivos[0]["duracao_segundos"]
                
                conteudo.append({
                    "tipo": "arquivo",
                    "titulo": item.get("title", "Sem título"),
                    "imagem": extrair_melhor_imagem(item.get("images", {}), tamanho_preferido="lg"),
                    "data_publicacao": formatar_data(data_bruta),
                    "duracao": duracao_api if duracao_api else formatar_duracao(duracao_seg),
                    "total_formatos": len(lista_arquivos),
                    "downloads": lista_arquivos
                })

    # 3. TRATAMENTO NORMAL (Para todas as outras pastas)
    else:
        url = f"{MEDIATOR_BASE_URL}/categories/{idioma}/{pasta}?detailed=1"
        dados = fazer_requisicao(url)

        categorias = dados.get("category", {}).get("subcategories", [])
        itens_midia = dados.get("category", {}).get("media", [])
        nome_atual = dados.get("category", {}).get("name", pasta)

        for cat in categorias:
            chave = cat.get("key")
            imagens = cat.get("images", {})
            
            imagem_final = extrair_melhor_imagem(imagens, tamanho_preferido="xl")
            if not imagem_final:
                imagem_final = obter_imagem_fallback(chave, idioma)
                
            conteudo.append({
                "tipo": "pasta",
                "nome": cat.get("name", "Sem Nome"),
                "chave": chave,
                "tem_subpastas": cat.get("hasSubcategories", False),
                "imagem": imagem_final
            })

        for item in itens_midia:
            lista_arquivos = extrair_todos_arquivos(item.get("files", []))
            if lista_arquivos:
                data_bruta = item.get("firstPublished", item.get("datetime", ""))
                duracao_api = item.get("durationFormattedHHMM")
                duracao_seg = lista_arquivos[0]["duracao_segundos"]

                conteudo.append({
                    "tipo": "arquivo",
                    "titulo": item.get("title", "Sem título"),
                    "imagem": extrair_melhor_imagem(item.get("images", {}), tamanho_preferido="lg"),
                    "data_publicacao": formatar_data(data_bruta),
                    "duracao": duracao_api if duracao_api else formatar_duracao(duracao_seg),
                    "total_formatos": len(lista_arquivos),
                    "downloads": lista_arquivos
                })

    return {
        "diretorio_atual": nome_atual,
        "chave_atual": pasta if pasta else "",
        "idioma": idioma,
        "total_itens": len(conteudo),
        "conteudo": conteudo
    }


# ==========================================
# Rota Visual (Front-end Integrado)
# ==========================================
@app.get("/navegador", response_class=HTMLResponse, summary="Interface Visual do Navegador")
def interface_visual():
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Navegador JW API</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; color: #333; }
            .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 20px; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
            h1 { margin: 0; font-size: 24px; color: #4a90e2; }
            button { background: #4a90e2; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-size: 14px; }
            button:hover { background: #357abd; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .search-box { padding: 8px 12px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px; min-width: 250px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
            .card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; text-align: center; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; background: #fafafa; }
            .card:hover { transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
            .card img { max-width: 100%; height: 120px; object-fit: cover; border-radius: 5px; margin-bottom: 10px; }
            .icon-pasta { font-size: 40px; margin-bottom: 10px; }
            .card-title { font-size: 14px; font-weight: bold; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
            .meta-info { font-size: 12px; color: #777; margin-top: 8px; margin-bottom: 8px; font-weight: 500; }
            .file-card { cursor: default; }
            .download-links { margin-top: 10px; display: flex; flex-direction: column; gap: 5px; }
            .download-links a { text-decoration: none; font-size: 12px; background: #28a745; color: white; padding: 5px; border-radius: 3px; }
            .download-links a:hover { background: #218838; }
            .loader { text-align: center; font-size: 18px; color: #666; margin: 50px 0; display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <button id="btn-voltar" disabled onclick="voltar()">⬅ Voltar</button>
                <h1 id="titulo-pasta">Carregando...</h1>
                <div>
                    <input type="text" id="input-busca" class="search-box" placeholder="Filtrar arquivos nesta pasta..." onkeyup="filtrarConteudo()">
                </div>
            </div>
            <div id="loader" class="loader">Buscando arquivos... ⏳</div>
            <div class="grid" id="grid-conteudo"></div>
        </div>

        <script>
            let historico = [];
            let chaveAtual = "";

            async function carregarPasta(chave_pasta) {
                document.getElementById('grid-conteudo').innerHTML = "";
                document.getElementById('input-busca').value = "";
                document.getElementById('loader').style.display = "block";
                
                try {
                    const url = chave_pasta ? `/api/explorar?pasta=${chave_pasta}` : '/api/explorar';
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    document.getElementById('titulo-pasta').innerText = data.diretorio_atual;
                    chaveAtual = data.chave_atual;
                    
                    document.getElementById('btn-voltar').disabled = historico.length === 0;

                    renderizarConteudo(data.conteudo);
                } catch (error) {
                    alert("Erro ao carregar os dados. Verifique o console.");
                    console.error(error);
                } finally {
                    document.getElementById('loader').style.display = "none";
                }
            }

            function renderizarConteudo(conteudo) {
                const grid = document.getElementById('grid-conteudo');
                
                conteudo.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    
                    if (item.tipo === "pasta") {
                        card.onclick = () => {
                            historico.push(chaveAtual);
                            carregarPasta(item.chave);
                        };
                        
                        let imgHtml = item.imagem ? `<img src="${item.imagem}" alt="capa">` : `<div class="icon-pasta">📁</div>`;
                        card.innerHTML = `${imgHtml}<p class="card-title">${item.nome}</p>`;
                        
                    } else if (item.tipo === "arquivo") {
                        card.classList.add('file-card');
                        let imgHtml = item.imagem ? `<img src="${item.imagem}" alt="capa">` : `<div class="icon-pasta">🎵</div>`;
                        
                        // Metadados de Data e Duração
                        let metaInfos = [];
                        if (item.data_publicacao) metaInfos.push(`📅 ${item.data_publicacao}`);
                        if (item.duracao) metaInfos.push(`⏱️ ${item.duracao}`);
                        let metaHtml = metaInfos.length > 0 ? `<div class="meta-info">${metaInfos.join(' &nbsp;•&nbsp; ')}</div>` : '';
                        
                        let linksHtml = item.downloads.map(dl => 
                            `<a href="${dl.url_download}" target="_blank">Baixar ${dl.formato.toUpperCase()} (${dl.resolucao ? dl.resolucao + 'p - ' : ''}${dl.tamanho_mb} MB)</a>`
                        ).join('');

                        card.innerHTML = `
                            ${imgHtml}
                            <p class="card-title">${item.titulo}</p>
                            ${metaHtml}
                            <div class="download-links">${linksHtml}</div>
                        `;
                    }
                    
                    grid.appendChild(card);
                });
            }

            function filtrarConteudo() {
                const termo = document.getElementById('input-busca').value.toLowerCase();
                const cards = document.querySelectorAll('#grid-conteudo .card');
                
                cards.forEach(card => {
                    const titulo = card.querySelector('.card-title').innerText.toLowerCase();
                    if (titulo.includes(termo)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }

            function voltar() {
                if (historico.length > 0) {
                    const chaveAnterior = historico.pop();
                    carregarPasta(chaveAnterior);
                }
            }

            window.onload = () => carregarPasta("");
        </script>
    </body>
    </html>
    """
    return html_content

# ==========================================
# Execução do Servidor
# ==========================================
if __name__ == "__main__":
    print("Iniciando a API Explorer na porta 8001...")
    uvicorn.run("api_midias:app", host="0.0.0.0", port=8001, reload=True)