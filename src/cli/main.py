from reporting.markdown_generator import generate_markdown_report
from orchestrator.coordinator import ReviewCoordinator
import asyncio
import typer
from structlog import get_logger
import structlog
import logging
from dotenv import load_dotenv

# Load .env from the current working directory
load_dotenv()


app = typer.Typer(help="MACR - Multi-Agent Code Review")
logger = get_logger()


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )


@app.command()
def review(
    file_path: str = typer.Argument(..., help="Path to the file to review"),
    output: str = typer.Option(
        "review_report.md", "--output", "-o", help="Output Markdown file"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    use_memory: bool = typer.Option(
        True, "--use-memory/--no-memory", help="Enable FAISS memory context"
    ),
):
    """Run a multi-agent code review on a file."""
    setup_logging(verbose)

    try:
        with open(file_path, "r") as f:
            code_content = f.read()
    except Exception as e:
        typer.secho(f"Failed to read file {file_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Initialize memory if requested
    memory_store = None
    if use_memory:
        try:
            from memory.faiss_store import FaissMemoryStore
            from memory.embeddings import EmbeddingService

            typer.secho("Initializing memory store...", fg=typer.colors.BLUE)
            embedding_service = EmbeddingService()
            memory_store = FaissMemoryStore(embedding_service=embedding_service)
        except ImportError:
            typer.secho(
                "Memory module not installed. Install with `pip install .[memory]`",
                fg=typer.colors.YELLOW,
            )
            memory_store = None

    coordinator = ReviewCoordinator(memory_store=memory_store)

    typer.secho(f"Starting review for {file_path}...", fg=typer.colors.CYAN)

    try:
        # Run async orchestrator
        final_report = asyncio.run(coordinator.review_file(file_path, code_content))
    except Exception as e:
        typer.secho(f"\nReview failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Generate report
    markdown_content = generate_markdown_report(final_report)
    with open(output, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    typer.secho(f"Review complete! Report saved to {output}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
