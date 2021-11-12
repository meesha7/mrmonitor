#!/usr/bin/env python3
import os

import arrow
import click
import dotenv
import gitlab
import rich

dotenv.load_dotenv()

gl = gitlab.Gitlab(os.getenv("GITLAB_URI"), private_token=os.getenv("PRIVATE_TOKEN"))


@click.group()
def cli():
    pass


@cli.command(help="List MRs from given projects (IDs separated by comma)")
@click.argument("project", required=True)
@click.option("--user", help="Filter for username")
def show(project, user):
    projects = project.split(",")
    first = True

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

            rich.print(f"  {iid_str} {title_str} [{upvotes_str} {downvotes_str}]")
            print(f"    Author: {mr.author['username']}")
            print(f"    {mr.web_url}")
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

            rich.print("    " + " | ".join(infos))
            print()


if __name__ == "__main__":
    cli()
