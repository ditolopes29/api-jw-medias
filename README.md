# API Explorer JW

Uma API robusta e navegador visual para explorar os conteúdos midiáticos (vídeos, áudios, etc.) do jw.org através da API pública do JW Mediator.

## 🚀 Funcionalidades

- **API de Backend (FastAPI):** Extrai, mescla e formata dados brutos da API oficial em uma estrutura JSON fácil de consumir.
- **Navegador Visual (Front-end Integrado):** Uma interface em HTML/JS servida pelo próprio FastAPI, permitindo a navegação visual pelas pastas, subpastas, reprodução, detalhes de arquivos e download de mídias de diferentes qualidades e formatos.
- **Crawler/Scanner Profundo:** O script `mapear_arvore.py` vasculha a árvore inteira de diretórios da API do site para mapear os endpoints e chaves.
- **Tratamento Inteligente de Mídias:** Seleciona automaticamente as melhores imagens (thumbnail fallback), calcula tempo de reprodução e mescla categorias de destaque.
- **Pronto para Deploy:** Configurado para deploy direto e rápido na Vercel (`vercel.json`).

## 🛠️ Tecnologias Utilizadas

- Python 3.9+
- FastAPI
- Uvicorn
- Requests

## 📦 Instalação e Execução Local

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd <nome-do-diretorio>
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o servidor da API:**
   ```bash
   python api_midias.py
   ```
   > O servidor iniciará na porta `8001`.

4. **Acesse a API:**
   - Documentação Interativa (Swagger): [http://localhost:8001/docs](http://localhost:8001/docs)
   - Interface de Navegação Visual: [http://localhost:8001/navegador](http://localhost:8001/navegador)

## 🔍 Mapeamento da Árvore de Diretórios (Crawler)

Para listar todas as categorias, subcategorias e chaves de API disponíveis no site, execute o script de varredura:

```bash
python mapear_arvore.py
```
Isso imprimirá a hierarquia no seu terminal, muito útil para achar uma chave de categoria específica para usar na API.

## ☁️ Deploy na Vercel

O projeto possui um arquivo `vercel.json` configurado para rodar o FastAPI como uma Serverless Function.

1. Tenha o [Vercel CLI](https://vercel.com/cli) instalado ou conecte seu repositório GitHub ao painel da Vercel.
2. Na raiz do projeto, execute:
   ```bash
   vercel
   ```
3. Siga os prompts para criar e publicar a aplicação.

## 📄 Licença e Termos de Uso

Este é um projeto não-oficial para propósitos educacionais, de pesquisa e de organização pessoal das mídias públicas disponíveis pelo JW.org. Todos os direitos e mídias pertencem a Watch Tower Bible and Tract Society of Pennsylvania.

Este projeto está em conformidade com os [Termos de Uso do jw.org](https://www.jw.org/pt/termos-de-uso/), que estabelecem:

> "Isso não proíbe a distribuição gratuita, sem fins comerciais, de aplicativos projetados para baixar arquivos eletrônicos como EPUB, PDF, MP3 e arquivos MP4 das áreas públicas deste site."
