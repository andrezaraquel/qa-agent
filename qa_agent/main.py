from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from crewai.tools import tool
import json, requests, os

llm = ChatAnthropic(model="claude-opus-4-5")

# --- Ferramentas ---
@tool
def ler_resultados_playwright(caminho: str) -> str:
    """Lê o arquivo JSON de resultados do Playwright e retorna um resumo."""
    with open(caminho) as f:
        results = json.load(f)
    total = results.get("stats", {})
    failed = [
        t for suite in results.get("suites", [])
        for t in suite.get("specs", [])
        if not t.get("ok")
    ]
    return json.dumps({
        "total": total,
        "falhas": [t["title"] for t in failed[:10]]
    })

@tool
def postar_comentario_pr(comentario: str) -> str:
    """Posta um comentário em um PR do GitHub."""
    token = os.getenv("GH_TOKEN")
    repo  = os.getenv("GITHUB_REPO")
    pr    = os.getenv("PR_NUMBER")

    if not all([token, repo, pr]):
        return "Erro: variáveis de ambiente GH_TOKEN, GITHUB_REPO ou PR_NUMBER não definidas."

    url  = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
    resp = requests.post(
        url,
        json={"body": comentario},
        headers={"Authorization": f"Bearer {token}"}
    )
    return "Comentario postado!" if resp.status_code == 201 else f"Erro: {resp.status_code} - {resp.text}"

# --- Agentes ---
analista = Agent(
    role="QA Analyst",
    goal="Analisar resultados de testes e identificar problemas criticos",
    backstory="Você é um QA senior com 10 anos de experiencia.",
    tools=[ler_resultados_playwright],
    llm=llm,
    verbose=True
)

redator = Agent(
    role="Technical Writer",
    goal="Transformar análise técnica em relatório claro para o time",  # ← corrigido
    backstory="Você escreve relatórios que devs e POs conseguem entender.",
    tools=[postar_comentario_pr],
    llm=llm,
    verbose=True
)

# --- Tarefas ---
tarefa_analise = Task(
    description=(
        "Leia o arquivo em '{arquivo}' e identifique: "  # ← usa o input corretamente
        "total de testes, falhas críticas, padrões de erro."
    ),
    expected_output="JSON com: total, falhas, severidade, padrões identificados",
    agent=analista
)

tarefa_relatorio = Task(
    description="Com base na análise, escreva um comentário de PR profissional e poste no GitHub.",
    expected_output="Confirmação de que o comentário foi postado",
    agent=redator,
    context=[tarefa_analise]
)

# --- Crew ---
crew = Crew(
    agents=[analista, redator],
    tasks=[tarefa_analise, tarefa_relatorio],
    process=Process.sequential,
    verbose=True
)

result = crew.kickoff(inputs={'arquivo': 'playwright-report/results.json'})  # ← caminho correto
print(result)