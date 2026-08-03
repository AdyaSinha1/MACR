import asyncio
import time
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

from orchestrator.coordinator import ReviewCoordinator
from memory.embeddings import EmbeddingService
from memory.faiss_store import FaissMemoryStore

app = typer.Typer(help="MACR Evaluation Script")
console = Console()

@app.command()
def run_eval(
    file_path: str = typer.Argument(..., help="Path to sample file to evaluate")
):
    """Runs an evaluation comparing MACR execution metrics."""
    try:
        with open(file_path, 'r') as f:
            code_content = f.read()
    except Exception as e:
        console.print(f"[bold red]Failed to read {file_path}: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold cyan]Evaluating MACR on:[/bold cyan] {file_path}")
    
    # Initialize Memory
    embedding_service = EmbeddingService()
    memory_store = FaissMemoryStore(embedding_service=embedding_service)
    coordinator = ReviewCoordinator(memory_store=memory_store)
    
    start_time = time.time()
    report = asyncio.run(coordinator.review_file(file_path, code_content))
    duration = time.time() - start_time
    
    # Build Metrics Table
    table = Table(title="MACR Pipeline Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Execution Time", f"{duration:.2f} seconds")
    table.add_row("Total Initial Findings", str(len(report.findings) + int(report.agent_agreement * len(report.findings))))
    table.add_row("Resolved Findings", str(len(report.findings)))
    table.add_row("Redundancy Reduction", f"{report.agent_agreement * 100:.1f}%")
    table.add_row("Overall Confidence", f"{report.total_confidence * 100:.1f}%")
    
    console.print(table)
    console.print("\n[bold green]Evaluation Complete.[/bold green]")

if __name__ == "__main__":
    app()
