"""
Before/after demo for the Incident Response Agent.

Shows the same incident:
1. Without Hindsight memory
2. With Hindsight memory

Run:
    python demo.py

Make sure you have already run:
    python ingest.py
"""

from rich.console import Console
from rich.panel import Panel

from agent import diagnose


console = Console()


NEW_INCIDENT = (
    "Checkout API is returning intermittent 502s again, started about 10 "
    "minutes ago. We're seeing it spike right after that promo email went "
    "out this morning. p99 latency on /checkout/create is climbing fast."
)


def main():

    # ---------------------------------------------------------
    # INCIDENT
    # ---------------------------------------------------------

    console.print(
        Panel(
            f"[bold]{NEW_INCIDENT}[/bold]",
            title="🚨 NEW INCIDENT",
            border_style="red",
        )
    )

    # ---------------------------------------------------------
    # WITHOUT MEMORY
    # ---------------------------------------------------------

    console.print(
        "\n[bold yellow]1. WITHOUT HINDSIGHT MEMORY[/bold yellow]"
    )

    console.print(
        "[dim]Agent is diagnosing from general knowledge only...[/dim]\n"
    )

    without_memory = diagnose(
        NEW_INCIDENT,
        use_memory=False
    )

    console.print(
        Panel(
            without_memory["diagnosis"],
            title="🤖 Cold-Start Diagnosis",
            border_style="yellow",
        )
    )

    # ---------------------------------------------------------
    # WITH MEMORY
    # ---------------------------------------------------------

    console.print(
        "\n[bold cyan]2. WITH HINDSIGHT MEMORY[/bold cyan]"
    )

    console.print(
        "[dim]Agent is recalling previous incidents from Hindsight...[/dim]\n"
    )

    with_memory = diagnose(
        NEW_INCIDENT,
        use_memory=True
    )

    if with_memory["memories"]:

        console.print(
            Panel(
                "\n\n".join(with_memory["memories"]),
                title=(
                    f"🧠 Hindsight Memory "
                    f"({len(with_memory['memories'])} matches)"
                ),
                border_style="cyan",
            )
        )

    else:

        console.print(
            Panel(
                "No relevant memories found.",
                title="🧠 Hindsight Memory",
                border_style="yellow",
            )
        )

    console.print(
        Panel(
            with_memory["diagnosis"],
            title="🚀 Memory-Grounded Diagnosis",
            border_style="green",
        )
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    console.print(
        Panel(
            "WITHOUT MEMORY → Generic diagnosis\n\n"
            "WITH HINDSIGHT → Recalls past incidents and "
            "uses team history to improve the diagnosis.",
            title="💡 WHAT HINDSIGHT ADDS",
            border_style="magenta",
        )
    )


if __name__ == "__main__":
    main()