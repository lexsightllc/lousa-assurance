# SPDX-License-Identifier: MPL-2.0
"""Lousa command-line interface for risk assessment and assurance tracking.

Lousa provides tools for evaluating risk notes, generating reports, and tracking
risk over time using Bayesian reasoning with temporal decay.

Examples:

    # Validate a risk note file
    lousa validate examples/notes/security_risk.yaml

    # Evaluate a risk note and save results
    lousa run examples/notes/security_risk.yaml --output-dir ./results

    # Generate a JSON schema for risk notes
    lousa schema --output risk_note.schema.json

    # Generate a GSN diagram for a risk note
    lousa gsn examples/notes/security_risk.yaml --output-dir ./diagrams
"""
from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .eval import (
    EvaluationError,
    NoteEvaluationResult,
    Posture,
    evaluate_note,
)
from .gsn import generate_gsn_diagram
from .logging import bind_context, bind_trace, configure_logging, get_logger
from .models import RiskNote
from .notebook import generate_notebook
from .provenance import capture_provenance, format_provenance, save_provenance

# Configure rich console
console = Console()

# Create the Typer app
app = typer.Typer(
    name="lousa",
    help="Lousa: A framework for evaluating temporal and epistemic assurance claims",
    no_args_is_help=True,
)

# Configure structured logging for CLI usage
configure_logging()
TRACE_ID = bind_trace()
bind_context(subsystem="cli")
cli_logger = get_logger(__name__).bind(subsystem="cli")
cli_logger.info("cli-session-start", trace_id=TRACE_ID)


class OutputFormat(str, Enum):
    """Supported output formats for the CLI."""
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    NOTEBOOK = "notebook"  # Special format for Jupyter notebooks


def print_validation_errors(errors: list[dict[str, Any]]) -> None:
    """Pretty-print validation errors to the console."""
    from rich.table import Table
    
    table = Table(
        "Field", "Error", 
        title="[red]Validation Errors", 
        header_style="bold red",
        border_style="red"
    )
    
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        table.add_row(field, error["msg"])
    
    console.print(table)


@app.command()
def notebook(
    path: Annotated[
        Path,
        typer.Option(..., "--path", "-p", help="Path to the YAML risk note"),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            ".",
            "--output-dir",
            "-o",
            help="Directory to save the notebook",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ],
    include_yaml: Annotated[
        bool,
        typer.Option(True, help="Include the full YAML specification in the notebook"),
    ],
    include_gsn: Annotated[
        bool,
        typer.Option(True, help="Generate and include GSN diagram in the notebook"),
    ],
) -> None:
    """Generate a Jupyter notebook for a risk assessment.
    
    This command creates a self-contained Jupyter notebook that documents the
    complete evaluation of a risk note, including the input specification,
    evaluation results, visualizations, and provenance information.
    """
    try:
        with console.status("[bold blue]Generating notebook..."):
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Load and validate the risk note
            try:
                with path.open() as f:
                    data = yaml.safe_load(f)
                note = RiskNote.model_validate(data)
            except Exception as e:
                console.print(f"[red]Error loading risk note: {e}")
                raise typer.Exit(1) from e
            
            # Generate the notebook
            notebook_path = generate_notebook(
                note=note,
                output_dir=output_dir,
                include_yaml=include_yaml,
                include_gsn=include_gsn,
            )
            
            console.print(f"[green]✓ Notebook generated: {notebook_path}")
            
    except Exception as e:
        console.print(f"[red]Error generating notebook: {e}")
        if __debug__:  # Only show traceback in debug mode
            import traceback
            traceback.print_exc()
        if isinstance(e, typer.Exit):
            raise
        raise typer.Exit(1) from e


@app.command()
def provenance(
    path: Annotated[
        Path,
        typer.Option(None, "--path", "-p", help="Path to the YAML risk note"),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            None,
            "--output",
            "-o",
            help="Save provenance to this file (default: print to stdout)",
            dir_okay=False,
        ),
    ],
    format: Annotated[
        OutputFormat,
        typer.Option(OutputFormat.TEXT, "--format", "-f", help="Output format", case_sensitive=False),
    ],
    include_dependencies: Annotated[
        bool,
        typer.Option(True, help="Include package dependency information"),
    ],
) -> None:
    """Generate and display provenance information.
    
    This command captures and displays detailed information about the execution
    environment, dependencies, and input files to support reproducibility and
    auditability of risk assessments.
    """
    try:
        with console.status("[bold blue]Capturing provenance..."):
            # Capture provenance
            prov = capture_provenance(
                note_path=path,
                include_dependencies=include_dependencies,
            )
            
            # Format the output
            if format == OutputFormat.NOTEBOOK:
                console.print("[yellow]Notebook format not supported for provenance command")
                format = OutputFormat.TEXT
                
            output_text = format_provenance(prov, format=format)
            
            # Save to file or print to stdout
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(output_text)
                console.print(f"[green]✓ Provenance saved to {output}")
            else:
                console.print(output_text)
                
    except Exception as e:
        console.print(f"[red]Error capturing provenance: {e}")
        if isinstance(e, typer.Exit):
            raise
        raise typer.Exit(1) from e


@app.command()
def validate(
    path: Annotated[
        Path,
        typer.Option(..., "--path", "-p", help="Path to the YAML risk note"),
    ],
    verbose: Annotated[
        bool,
        typer.Option(False, "--verbose", "-v", help="Show detailed validation output"),
    ],
) -> None:
    """Validate a YAML risk note against the schema and data model.
    
    This command checks that the provided YAML file conforms to the expected
    structure and contains valid values for all required fields.
    """
    try:
        with console.status("[bold blue]Validating risk note..."):
            # Read and parse the YAML file
            try:
                with path.open() as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                console.print(f"[red]Error parsing YAML: {e}")
                raise typer.Exit(1) from e
            
            # Validate against the Pydantic model
            try:
                RiskNote.model_validate(data)
                console.print("[green]✓ Risk note is valid")
            except Exception as e:
                if hasattr(e, "errors") and verbose:
                    print_validation_errors(e.errors())
                console.print(f"[red]✗ Validation failed: {e}")
                raise typer.Exit(1) from e
                
    except Exception as e:
        console.print(f"[red]Error during validation: {e}")
        raise typer.Exit(1) from e


def format_posterior(p: float) -> str:
    """Format a posterior probability for display."""
    if p < 0.1:
        return f"[green]{p:.1%}[/]"
    elif p < 0.5:
        return f"[yellow]{p:.1%}[/]"
    else:
        return f"[red]{p:.1%}[/]"


def format_posture(posture: Posture) -> str:
    """Format a posture with appropriate color coding."""
    styles = {
        Posture.ACCEPTABLE: "[green]ACCEPTABLE[/]",
        Posture.CONDITIONAL: "[yellow]CONDITIONAL[/]",
        Posture.BLOCKING: "[red]BLOCKING[/]",
        Posture.EXPIRED: "[dim]EXPIRED[/]",
    }
    return styles.get(posture, str(posture))


def print_evaluation_summary(result: NoteEvaluationResult) -> None:
    """Print a summary of the evaluation results to the console."""
    # Overall result
    console.print("\n[bold]Evaluation Summary[/]")
    console.print(f"Note: [bold]{result['title']}[/] ({result['note_id']})")
    console.print(f"Overall Posture: {format_posture(result['overall_posture'])}")
    
    # Claims table
    table = Table(
        "ID", "Title", "Posture", "Posterior", "Evidence",
        title="[bold]Claims[/]",
        header_style="bold",
        box=None,
    )
    
    for claim in result["claims"]:
        table.add_row(
            claim.claim_id,
            claim.title,
            format_posture(claim.posture),
            format_posterior(claim.posterior),
            str(len(claim.contributions)),
        )
    
    console.print(table)
    
    # Top recommendations
    if result["recommendations"]:
        console.print("\n[bold]Top Recommendations[/]")
        for i, rec in enumerate(result["recommendations"][:3], 1):
            console.print(
                f"{i}. [bold]{rec['title']}[/] (Δp/hour: {abs(rec['expected_delta'])/rec['cost_hours']:.3f})"
                f"\n   For claim: {rec['claim_title']}"
                f"\n   Expected Δp: {rec['expected_delta']:+.3f}, Cost: {rec['cost_hours']} hours"
            )


@app.command()
def run(
    path: Annotated[
        Path,
        typer.Option(..., "--path", "-p", help="Path to the YAML risk note"),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            ".",
            "--output-dir",
            "-o",
            help="Directory to save output files",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ],
    output_format: Annotated[
        OutputFormat,
        typer.Option(OutputFormat.TEXT, "--format", "-f", help="Output format", case_sensitive=False),
    ],
    now: Annotated[
        str | None,
        typer.Option(
            None,
            help="Evaluation timestamp (ISO 8601 format, e.g., 2025-01-01T12:00:00Z)",
        ),
    ],
    create_notebook: Annotated[
        bool,
        typer.Option(
            False,
            "--notebook",
            "-n",
            help="Generate a Jupyter notebook with the evaluation results",
        ),
    ],
    notebook_output: Annotated[
        Path | None,
        typer.Option(
            None,
            "--notebook-output",
            help="Directory to save the notebook (default: same as --output-dir)",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ],
) -> None:
    """Evaluate a risk note and generate reports.

    This command evaluates the specified risk note, applies temporal decay to
    evidence, computes risk postures, and generates output artifacts.
    """
    cli_logger.info(
        "cli-run-start",
        command="run",
        note_path=str(path),
        output_dir=str(output_dir),
        output_format=output_format.value,
        create_notebook=create_notebook,
    )
    try:
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse evaluation time
        eval_time = datetime.now().astimezone()
        if now:
            try:
                from dateutil.parser import isoparse
                eval_time = isoparse(now)
            except ValueError as e:
                console.print(f"[yellow]Warning: Invalid timestamp '{now}': {e}. Using current time.")
        
        # Load and validate the risk note
        with console.status("[bold blue]Loading and validating risk note..."):
            try:
                with path.open() as f:
                    note_data = yaml.safe_load(f)
                note = RiskNote.model_validate(note_data)
            except Exception as e:
                console.print(f"[red]Error loading risk note: {e}")
                raise typer.Exit(1) from e
        
        # Evaluate the note
        with console.status("[bold blue]Evaluating risk note..."):
            try:
                result = evaluate_note(note, now=eval_time)
            except EvaluationError as e:
                console.print(f"[red]Evaluation error: {e}")
                raise typer.Exit(1) from e
        
        # Generate output files
        with console.status("[bold blue]Generating output files..."):
            # Save JSON result
            result_path = output_dir / f"{note.id}_result.json"
            with result_path.open("w") as f:
                json.dump(result, f, indent=2, default=str)

            nb_path = None
            if create_notebook:
                try:
                    nb_dir = notebook_output or output_dir
                    nb_path = generate_notebook(note, output_dir=nb_dir)
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to generate notebook: {e}")

            # Capture provenance
            try:
                prov = capture_provenance(path)
                save_provenance(prov, output_dir / f"provenance_{note.id}.json")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to capture provenance: {e}")
        
        # Print summary
        console.print("\n[bold green]✓ Evaluation complete[/]")
        print_evaluation_summary(result)

        console.print("\n[bold]Output Files:[/]")
        console.print(f"• JSON results: [blue]{result_path.absolute()}[/]")
        if nb_path:
            console.print(f"• Notebook: [blue]{nb_path.absolute()}[/]")

        cli_logger.info(
            "cli-run-complete",
            command="run",
            note_id=note.id,
            output_dir=str(output_dir),
            overall_posture=result["overall_posture"].value,
            notebook_generated=bool(nb_path),
        )

        # Set exit code based on overall posture
        if result["overall_posture"] == Posture.BLOCKING:
            raise typer.Exit(3)
        elif result["overall_posture"] == Posture.CONDITIONAL:
            raise typer.Exit(2)

    except Exception as e:
        console.print(f"[red]Error: {e}")
        if __debug__:  # Only show traceback in debug mode
            import traceback
            traceback.print_exc()
        cli_logger.exception("cli-run-error", command="run", error=str(e))
        raise typer.Exit(1) from e



@app.command()
def schema(
    output: Annotated[
        Path | None,
        typer.Option(
            None,
            "--output",
            "-o",
            help="Write schema to this file instead of stdout",
            dir_okay=False,
        ),
    ],
    format: Annotated[
        OutputFormat,
        typer.Option(OutputFormat.JSON, "--format", "-f", help="Output format", case_sensitive=False),
    ],
) -> None:
    """Generate and display the JSON Schema for risk notes.
    
    This command outputs the JSON Schema that defines the structure of valid
    risk note files. The schema can be used for validation in other tools or
    for documentation purposes.
    """
    try:
        # Generate the JSON Schema from the Pydantic model
        schema = RiskNote.model_json_schema()
        
        # Add top-level description if not present
        if "description" not in schema:
            schema["description"] = "A Lousa risk note for tracking assurance claims and evidence"
        
        # Format the output
        if format == OutputFormat.JSON:
            output_str = json.dumps(schema, indent=2)
        elif format == OutputFormat.YAML:
            import yaml
            output_str = yaml.dump(schema, sort_keys=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Write to file or print to stdout
        if output:
            output.write_text(output_str)
            console.print(f"[green]✓ Schema written to {output.absolute()}")
        else:
            console.print(output_str)
            
    except Exception as e:
        console.print(f"[red]Error generating schema: {e}")
        raise typer.Exit(1) from e


@app.command()
def gsn(
    path: Annotated[
        Path,
        typer.Option(..., "--path", "-p", help="Path to the YAML risk note"),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            ".",
            "--output-dir",
            "-o",
            help="Directory to save the GSN diagram",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ],
    format: Annotated[
        str,
        typer.Option("svg", "--format", "-f", help="Output format (svg, png, pdf, etc.)"),
    ],
) -> None:
    """Generate a Goal Structuring Notation (GSN) diagram for a risk note.
    
    This command creates a visual representation of the risk note's structure
    using GSN, showing how claims are supported by evidence and assumptions.
    """
    try:
        # Load and validate the risk note
        with console.status("[bold blue]Loading risk note..."):
            with path.open() as f:
                note_data = yaml.safe_load(f)
            note = RiskNote.model_validate(note_data)
        
        # Generate the GSN diagram
        with console.status(f"[bold blue]Generating GSN diagram in {format.upper()} format..."):
            output_path = generate_gsn_diagram(note, output_dir=output_dir, format=format)
        
        console.print(f"[green]✓ GSN diagram saved to {output_path.absolute()}")
        
    except Exception as e:
        console.print(f"[red]Error generating GSN diagram: {e}")
        if __debug__:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1) from e


def main() -> None:
    """Entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    main()
