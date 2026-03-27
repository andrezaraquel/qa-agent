import json
import os
import requests
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Ferramentas ---

def ler_resultados_playwright(caminho: str) -> dict:
    """Lê o arquivo JSON de resultados do Playwright e retorna um resumo."""
    if not os.path.exists(caminho):
        return {"erro": f"Arquivo não encontrado: {caminho}"}

    with open(caminho) as f:
        results = json.load(f)

    total = results.get("stats", {})
    failed = [
        t for suite in results.get("suites", [])
        for t in suite.get("specs", [])
        if not t.get("ok")
    ]
    return {
        "total": total,
        "falhas": [t["title"] for t in failed[:10]]
    }


def postar_comentario_pr(comentario: str) -> str:
    """Posta um comentário em um PR do GitHub."""
    token = os.getenv("GH_TOKEN")
    repo  = os.getenv("GITHUB_REPO")
    pr    = os.getenv("PR_NUMBER")

    if not all([token, repo, pr]):
        return "Erro: variáveis GH_TOKEN, GITHUB_REPO ou PR_NUMBER não definidas."

    url  = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
    resp = requests.post(
        url,
        json={"body": comentario},
        headers={"Authorization": f"Bearer {token}"}
    )
    return "Comentario postado!" if resp.status_code == 201 else f"Erro: {resp.status_code} - {resp.text}"


# --- Agente 1: Analista ---

def analisar_resultados(arquivo: str) -> str:
    """Usa Claude para analisar os resultados dos testes."""
    dados = ler_resultados_playwright(arquivo)

    if "erro" in dados:
        return f"Erro ao ler arquivo: {dados['erro']}"

    prompt = f"""You are a senior QA engineer with 10 years of experience.
Analyze the following Playwright test results and identify:
- Total tests run, passed, and failed
- Critical failures
- Error patterns
- Severity level (low / medium / high / critical)

Test results:
{json.dumps(dados, indent=2)}

Respond with a structured JSON containing: total, passed, failed, severidade, falhas, padroes.
"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# --- Agente 2: Redator ---

def gerar_e_postar_relatorio(analise: str) -> str:
    """Usa Claude para transformar a análise em comentário de PR e posta no GitHub."""

    prompt = f"""You are a technical writer who creates clear reports for developers and product managers.
Based on the QA analysis below, write a professional GitHub PR comment in markdown.

The comment should include:
- A clear summary with emoji indicators (✅ ❌ ⚠️)
- A table of failed tests with severity
- Identified error patterns
- A suggested next step

QA Analysis:
{analise}

Write only the markdown comment, nothing else.
"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    comentario = response.content[0].text
    print("\n--- Comentário gerado ---")
    print(comentario)
    print("------------------------\n")

    return postar_comentario_pr(comentario)


# --- Execução principal ---

if __name__ == "__main__":
    arquivo = "playwright-report/results.json"

    print("🔍 Analisando resultados dos testes...")
    analise = analisar_resultados(arquivo)
    print("Análise concluída.")
    print(analise)

    print("\n📝 Gerando e postando relatório no PR...")
    resultado = gerar_e_postar_relatorio(analise)
    print(resultado)