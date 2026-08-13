import requests

# URL base oficial da API
MEDIATOR_BASE_URL = "https://b.jw-cdn.org/apis/mediator/v1"

def varrer_niveis(chave_pai, idioma, nivel):
    """
    Função recursiva que entra nas pastas e subpastas.
    """
    url = f"{MEDIATOR_BASE_URL}/categories/{idioma}/{chave_pai}?detailed=0"
    
    try:
        resposta = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        
        if resposta.status_code != 200:
            return

        dados = resposta.json()
        subcategorias = dados.get("category", {}).get("subcategories", [])
        
        for sub in subcategorias:
            nome = sub.get("name", "Sem Nome")
            nova_chave = sub.get("key", "")
            tem_sub = sub.get("hasSubcategories", False)
            
            # Formatação visual
            espaco = "    " * nivel
            icone = "📂" if tem_sub else "▶️"
            
            print(f"{espaco}{icone} {nome} -> (Chave: {nova_chave})")
            
            # Se a pasta tiver subpastas, entra nela
            if tem_sub and nova_chave:
                varrer_niveis(nova_chave, idioma, nivel + 1)
                
    except Exception as e:
        print(f"Erro ao ler a chave {chave_pai}: {e}")

def mapear_raiz_absoluta(idioma="T"):
    """
    Inicia a varredura a partir da raiz total do idioma.
    """
    # Endpoint sem especificar a categoria, pega a raiz do idioma
    url_raiz = f"{MEDIATOR_BASE_URL}/categories/{idioma}?detailed=0"
    
    try:
        resposta = requests.get(url_raiz, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        
        if resposta.status_code != 200:
            print("Não foi possível acessar a raiz do servidor.")
            return
            
        dados = resposta.json()
        
        # A raiz retorna as grandes áreas do site na chave 'categories'
        categorias_mestras = dados.get("categories", [])
        
        for cat in categorias_mestras:
            nome = cat.get("name", "Sem Nome")
            chave = cat.get("key", "")
            
            print(f"\n🌍 CATEGORIA MESTRA: {nome} -> (Chave: {chave})")
            print("="*60)
            
            if chave:
                varrer_niveis(chave, idioma, nivel=1)
                
    except Exception as e:
        print(f"Erro fatal: {e}")

# ==========================================
# Execução do Crawler
# ==========================================
if __name__ == "__main__":
    print("Iniciando varredura ABSOLUTA no servidor do jw.org...\n")
    
    # Inicia a varredura profunda na raiz (vai demorar um pouco mais porque vai ler o site todo)
    mapear_raiz_absoluta(idioma="T")
    
    print("\nVarredura concluída! Use a função de busca do seu terminal (Ctrl+F) para achar a Trilha Sonora.")