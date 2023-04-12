#!/usr/bin/env python3
import os
import re

import arrow
import click
import dotenv
import gitlab
import rich
from rich.console import Console

dotenv.load_dotenv()

gl = gitlab.Gitlab(os.getenv("GITLAB_URI"), private_token=os.getenv("PRIVATE_TOKEN"))
JIRA_URL = os.getenv("JIRA_URL", "").removesuffix("/")
JIRA_REGEX = [re.compile(regex) for regex in os.getenv("JIRA_REGEX", "").split(",")]


def _get_jira_link(mr) -> str | None:
    if JIRA_URL and JIRA_REGEX:
        for pattern in JIRA_REGEX:
            if m := pattern.search(mr.title):
                issue_id = m.group(1)
                return issue_id

def _get_colored_pipeline_status(pipeline) -> str:
    match pipeline.status:
        case "failed":
            color = "red"
        case "pending":
            color = "yellow"
        case "running":
            color = "cyan"
        case "success":
            color = "green"
        case _:
            color = "grey"

    return f"[{color}]{pipeline.status}[/{color}]"


@click.group()
def cli():
    pass


@cli.command(help="List MRs from given projects (IDs separated by comma)")
@click.argument("project_ids", required=True)
@click.option("--user", help="Filter for username")
def show(project_ids, user):
    """Show MRs for a single user across projects."""
    projects = project_ids.split(",")
    first = True
    console = Console(highlight=False)

    for project_id in projects:
        project = gl.projects.get(project_id)
        mrs = project.mergerequests.list(state="opened", author_username=user)

        if not first:
            print()
            first = False

        rich.print(f"[bold blue]{project.path_with_namespace}[/bold blue]")

        if not mrs:
            print("  No merge requests matching the criteria")
            print()
            continue

        for mr in mrs:
            # MR info
            iid_str = f"[bold red]!{mr.iid}[/bold red]"
            title_str = f"[yellow]{mr.title}[/yellow]"

            upvotes_str = downvotes_str = "0"

            if mr.upvotes:
                upvotes_str = f"[bold green]+{mr.upvotes}[/bold green]"

            if mr.downvotes:
                downvotes_str = f"[bold red]-{mr.downvotes}[/bold red]"

            approvals = mr.approvals.get()

            approved = (
                "[bold green]Yes[/bold green]"
                if approvals.approved_by
                else "[bold red]No[/bold red]"
            )
            approvers = (
                "by " + ", ".join([ap["user"]["username"] for ap in approvals.approved_by])
                if approvals.approved_by
                else ""
            )

            console.print(f"  {iid_str} {title_str} [{upvotes_str} {downvotes_str}]")
            console.print(f"    Author:   {mr.author['username']}")
            console.print(f"    Approved: {approved} {approvers}")
            console.print(f"    URL:      [link={mr.web_url}]MR {mr.iid}[/link]")

            if issue_id := _get_jira_link(mr):
                console.print(f"    JIRA:     [link={JIRA_URL}/{issue_id}]{issue_id}[/link]")

            pipelines = mr.pipelines.list()

            if pipelines:
                last_pipeline = sorted(pipelines, key=lambda x: x.id)[-1]
                console.print(f"    Pipeline: {_get_colored_pipeline_status(last_pipeline)}")

            print()

            # Dates
            created = arrow.get(mr.created_at)
            updated = arrow.get(mr.updated_at)
            age = arrow.now() - created
            since_update = arrow.now() - updated

            infos = [
                f"[cyan]Created:[/cyan] {created.humanize()}",
            ]

            if age.days >= 7:
                infos.append(f"[cyan]Age:[/cyan] [bold red]{age.days} days[/bold red]")
            elif age.days >= 3:
                infos.append(f"[cyan]Age:[/cyan] [bold yellow]{age.days} days[/bold yellow]")
            else:
                infos.append(f"[cyan]Age:[/cyan] [bold green]{age.days} days[/bold green]")

            if since_update.days >= 3:
                infos.append(
                    f"[cyan]Since update:[/cyan] [bold red]{since_update.days} days[/bold red]"
                )
            elif since_update.days >= 1:
                infos.append(
                    f"[cyan]Since update:[/cyan] [bold yellow]{since_update.days} days[/bold yellow]"
                )
            else:
                infos.append(
                    f"[cyan]Since update:[/cyan] [bold green]{since_update.days} days[/bold green]"
                )

            console.print("    " + " | ".join(infos))
            print()


if __name__ == "__main__":
    if not os.getenv("GITLAB_URI"):
        rich.print("[bold red]GITLAB_URI not configured[/bold red]")
        exit(1)

    if not os.getenv("PRIVATE_TOKEN"):
        rich.print("[bold red]PRIVATE_TOKEN not configured[/bold red]")
        exit(1)

    cli()
